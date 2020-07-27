import requests
from bs4 import BeautifulSoup

def scrape_gallup_environment():
    '''scrapes gallup.com environment section. Scraping HTML. As of this writing (7/27/2020) there were
    only tables and graphs on the page. Details of data representation in _parse_graph_summaries
    and _parse_tables docstrings'''
    page = requests.get("https://news.gallup.com/poll/1615/environment.aspx").text
    soup = BeautifulSoup(page, 'lxml')
    images = soup.find_all("div", {"class":"sggt-image"})
    parsed_summaries = _parse_graph_summaries(images)
    tables = soup.find_all("figure", {"class":"figure-table"})
    parsed_tables =_parse_tables(tables)
    return parsed_summaries, parsed_tables

def _parse_tables(tables):
    '''Tables all follow basically the same form with one variation: some tables have sub-groups and
    some do not. All the tables have a question at the top which the table summarizes responses to.
    The tables without groups then have a series of columns with responses and rows labled by date.
    Tables with groups follow the same basic form except they also have sub-groups with headings
    relevent to the group below them. All tables are organized into dictionaries of the following form
    (for no groups): {'description': description, 'heading1':first response, ...'headingN': nth response:
    {'row1': {'Value': row 1 value, 'Unit': row 1 unit}}...{'row n': {'Value': row n value, 'Unit': row n unit}}}
    or for grouped tables: {'description': description, 'subheading1': first subheading: {'heading1': first heading:
    {'Value': value of heading one in subgroup 1, 'Unit': unit of first value in first group}, ...'headingN':
    {'Value': value of heading N in subgroup N, 'Unit': unit of Nth value in Nth group}}...'subheadingN':{...}}'''
    table_dicts = []
    for table in tables:
        if len(table.find_all("th", {"scope" : "rowgroup"})) >= 1:
            table_dict = _parse_table_with_groups(table)
        else:
            table_dict = _parse_table_without_groups(table)
        table_dicts.append(table_dict)
    return table_dicts

def _parse_graph_summaries(images):
    summary_dicts = []
    for image in images:
        summary = _parse_graph_summary(image)
        summary_dicts.append(summary)
    return summary_dicts

def _parse_graph_summary(image):
    '''Line graph, desc contains a description of the graph while f1 and f2 represent fields related
    to lines on the graph. In both cases only two lines are represented in the summary while on one graph
    there are three lines. The sumarry contains the description, the name of each of two lines, the peak value
    of that line (in percent of respondants) and the year of that peak as well as the last year data was
    collected and the value for each of the two lines at that point'''
    space_split = image.img['alt'].split(' ')
    desc =  (" ").join(space_split[:7])
    f1 = space_split[8:11]
    f2 = space_split[11:14]
    end_data_values = space_split[14:]
    f1_str = f1[1][:-1]
    f2_str = f2[1][:-1]
    latest_dict = {'Latest': {'Year': end_data_values[0][:-1], f1_str: end_data_values[1], f2_str: end_data_values[3]}}
    f1_dict = {'High': f1[0], 'Year': f1[2][:-1]}
    f2_dict = {'High':f2[0], 'Year':f2[2][:-1]}
    return {'description': desc, f1_str: f1_dict, f2_str: f2_dict, 'latest_data': latest_dict}

def _parse_table_with_groups(table):
    table_dict = {}
    groups = table.find_all("tbody")
    group_names = table.find_all("th", {"scope": "rowgroup"})
    table_dict['description'] = table.div.text
    for group, name in zip(groups, group_names):
        table_dict[name.text] = _get_values_for_group(group)
    return table_dict

def _get_values_for_group(group):
    sub_headings = group.find_all("th", {"scope":"row"})
    inner_dict = {}
    for sh in sub_headings:
        value_list = group.find_all("td")[1:]
        inner_dict[sh.text] = _fill_values(value_list)
    return inner_dict

def _fill_values(value_list):
    value_dict = {}
    for value in value_list:
        try:
            value_dict[value['data-th']]={'Value':value.text, 'Unit':value['data-thunit']}
        except KeyError:
            value_dict[value['data-th']] = {'Value': value.text, 'Unit': None}
    return value_dict

def _parse_table_without_groups(table):
    desc = table.figcaption.text.strip()
    rows = table.tbody.find_all("tr")
    table_dict = {'description': desc}
    for row in rows:
        table_dict[row.th.text] = _get_values_for_row(row)
    return table_dict

def _get_values_for_row(row):
    row_dict = {}
    cols = row.find_all("td")
    _fill_values(cols)
    return row_dict

if __name__ == "__main__":
    scrape_gallup_environment()

import pandas as pd
import bs4
import requests
import lxml
'''
config file example:
auth_token
user_id
http:\\ip_adress_t4c_server
username
password
'''
my_file = open("config.txt", "r")

content = my_file.read()

config = content.split("\n")

my_file.close()


def login():
    url = config[2] + '/T4C/Content/Login.aspx'
    values = {'txtUserName': config[3],
              'txtPassword': config[4],
              'btnLogin_5': 'Login',
              '__EVENTARGUMENT': '',
              '__EVENTTARGET': ''}
    session = requests.Session()
    session.post(url, data=values)
    return session


def get_errors():
    url = config[2] + '/T4C/Content/AjaxRequest.aspx?Module=53&PageNo=1&MaxParams=9&0=2&1=1&MultiSort=2:1:1' \
                           '|&6=&5=2&7=&8=1,0,1'
    headers = {'Content-type': 'application/json'}
    '''
    < option value="3" > Сигнал для привлечения внимания < / option > 
    < option value="1" > Критическая тревога < / option > 
    < option value="4" > Доклад < / option > 
    < option value="5" > Сигнал тревоги по ритму < / option > 
    < option value="2" > Сигнал тревоги < / option >
    '''
    response = s.post(url, headers=headers, json={'autoRefresh': 'true'})
    # pd.options.display.width = 0
    # df = pd.read_html(response.text)
    soup = bs4.BeautifulSoup(response.content, features="lxml")

    tr = soup.find('tr')
    print(tr.find_all('td')[2].text)
    #    print(td.text)

    return response


def notificate():
    data = "test"
    teledata = {'text': data,
                'chat_id': config[1]}
    s.post('https://api.telegram.org/bot' + config[0] + '/sendmessage', data=teledata)


if __name__ == '__main__':
    s = login()

    get_errors()

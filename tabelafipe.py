#! python3
# Author: Vidal Salem Zeulum
# Description
#   This module performs data extraction (zero KM motorcicles data) from FIPE website. 
#   Stability obtained using selenium 4.19 .

from platform import system as osname 
from contextlib import contextmanager 
#from json import loads, dumps
from bs4 import BeautifulSoup 
import time
from selenium import webdriver 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

#from vsz_log import logger,log_formatter
from vsz_funcoes_diversas import  menu 

nome_arq_final = ".\dados_maisretorno.txt" #arquivo json onde os resultados são armazenados
nome_arq_parametros = "maisretorno_fundos.txt" #arquivo texto com fundos no formato json
MODULE_NAME = 'leitura_maisretorno'
SECONDS_TO_LOAD_SITE = 2
WAIT_TIME  = 0.5
ATTEMPTS = 4

@contextmanager 
def browser_connection():
#context manager para abrir e fechar um browser
    if osname() == 'Darwin': browser = webdriver.Safari()
    else: browser=webdriver.Chrome()#'C:\\Users\\vzebu\\Downloads\\chromedriver.exe')
    yield browser 
    
    try: browser.quit()
    except Exception as err:  err.args += tuple('====Browser was closed elsewhere!')



def try_x_times(func,error_message="",repeat=ATTEMPTS):
# executes a function (func) a number of times and raises an exception is an error happens
    for _ in range(repeat):
        try:
            time.sleep(WAIT_TIME * (_+1)) 
            func()
            break
        except Exception as err: 
            if _== repeat-1: original_error= (err.args[0] if len(err.args>0) else '')
        if _== repeat-1: raise RuntimeError( f'{error_message}\n{original_error}')  

def testes():
    with browser_connection() as browser: 
        browser.implicitly_wait(5)
        #load website
        command = lambda: browser.get ('https://veiculos.fipe.org.br')
        try: 
            try_x_times(func=command,error_message='Erro ao carregar website',repeat=1)
            browser.maximize_window()
        except Exception as err:
            print(err.args[0])
            return

        # acivate motorcycle panel
        command = lambda: browser.find_element(By.LINK_TEXT,"Consulta de Motos").click()
        try: try_x_times(func=command,error_message='Erro ao clicar em consulta de motos')
        except Exception as err:
            print(err.args[0])
            return
        command = lambda: browser.find_element(By.LINK_TEXT,"Pesquisa comum").click()
        try: try_x_times(func=command,error_message='Erro ao clicar em pesquisa comum')
        except Exception as err:
            print(err.args[0])
            return
        try:
    # finding brands, year and models fields
            xpath='//div[@class="chosen-container chosen-container-single" and @id="selectMarcamoto_chosen"]'
            brand_element = browser.find_element(By.XPATH,xpath)
            xpath='//div[@class="chosen-container chosen-container-single" and @id="selectAnomoto_chosen"]'
            year_element = browser.find_element(By.XPATH,xpath)
            xpath='//div[@class="chosen-container chosen-container-single" and @id="selectAnoModelomoto_chosen"]'
            model_element = browser.find_element(By.XPATH,xpath)
            brand_element.click()
            web_element=browser.switch_to.active_element
            web_element.send_keys('brp')
            web_element.send_keys(Keys.ENTER)
            year_element.click()
            web_element=browser.switch_to.active_element
            web_element.send_keys('zero km')
            web_element.send_keys(Keys.ENTER)
            model_element.click()
            web_element=browser.switch_to.active_element
            xpath='//li[@class="active-result"]'
            for model in browser.find_elements(By.XPATH,xpath): print(model.text,len(model.text))

            web_element.send_keys(Keys.ENTER)
            print(web_element.text)
            print(model_element.text, 'a')
            previous_text = ''
            while previous_text != model_element.text:
                print((previous_text := model_element.text)) 
                web_element.send_keys(Keys.ARROW_DOWN)
                web_element.send_keys(Keys.ARROW_DOWN)
                web_element.send_keys(Keys.ENTER)


        except Exception as err: print(err)


def leitura_fipe():

    def click_reset_button():
        xpath='//div[@class="button pesquisa clear" and @id="buttonLimparPesquisarmoto"]'
        browser.find_element(By.XPATH,xpath).click()
    

    with browser_connection() as browser: 
        browser.implicitly_wait(5)

        #load website
        command = lambda: browser.get ('https://veiculos.fipe.org.br')
        try: 
            try_x_times(func=command,error_message='Erro ao carregar website',repeat=1)
            browser.maximize_window()
        except Exception as err:
            print(err.args[0])
            return

        # acivate motorcycle panel
        command = lambda: browser.find_element(By.LINK_TEXT,"Consulta de Motos").click()
        try: try_x_times(func=command,error_message='Erro ao clicar em consulta de motos')
        except Exception as err:
            print(err.args[0])
            return
        command = lambda: browser.find_element(By.LINK_TEXT,"Pesquisa comum").click()
        try: try_x_times(func=command,error_message='Erro ao clicar em pesquisa comum')
        except Exception as err:
            print(err.args[0])
            return
        # finding brands, year and models fields
        try:
            xpath='//div[@class="chosen-container chosen-container-single" and @id="selectMarcamoto_chosen"]'
            brand_element = browser.find_element(By.XPATH,xpath)
            xpath='//div[@class="chosen-container chosen-container-single" and @id="selectAnomoto_chosen"]'
            year_element = browser.find_element(By.XPATH,xpath)
            xpath='//div[@class="chosen-container chosen-container-single" and @id="selectAnoModelomoto_chosen"]'
            model_element = browser.find_element(By.XPATH,xpath)
        except Exception as err:
            print('Falha ao tentar localizar elemento html da marca, modelo ou ano')
            return

        # retrieve list of motorcycle companies        
        try: 
            command = lambda: brand_element.click()
            try_x_times(func=command,error_message='Erro ao clicar na montadora para obter lista de montadoras')
            #web_element=browser.switch_to.active_element
            xpath='//div[@class="input" and @config="moto"]'
            brands=browser.find_element(By.XPATH,xpath).text.splitlines()
            brands = brands[1::]
            if len(brands) < 20: raise Exception('Erro: menos de 20 montadoras encontradas')
        except Exception as err:
            print(err.args[0])
            return
        #brands = ['brp']
        failures_on_process=[] #list o tuples indicating failures on (brand,) or (brand,model)
        with open('leitura_fipe.txt','w') as result_file:
            for brand in brands:
                # check if brand has Zero KM models
                try: 
                    command = lambda: brand_element.click()
                    try_x_times(func=command,error_message=f'Erro ao clicar na montadora para obter lista de montadoras: {brand}')
                    web_element=browser.switch_to.active_element
                    web_element.send_keys(brand)
                    web_element.send_keys(Keys.ENTER)
                    time.sleep(WAIT_TIME)
                    command = lambda: year_element.click()
                    try_x_times(func=command,error_message=f'Erro ao clicar no ano do modelo para obter modelos de {brand}')
                    xpath='//div[@class="input" and @config="moto" and @urlconsulta="ConsultarModelosAtravesDoAno"]'
                    years=browser.find_element(By.XPATH,xpath).text.splitlines()
                    if years[1] != 'Zero KM': continue
                    
                    # retrieving zero km models
                    web_element=browser.switch_to.active_element
                    web_element.send_keys('Zero KM')
                    web_element.send_keys(Keys.ENTER)
                    time.sleep(WAIT_TIME)
                    command = lambda: model_element.click()
                    try_x_times(func=command,error_message=f'Erro ao obter lista de modelos de {brand}')
                    xpath='//div[@class="input" and @config="moto" and @urlconsulta="ConsultarAnoModelo"]'
                    models=browser.find_element(By.XPATH,xpath).text.splitlines()[1:-1:]
                    # Getting models from another html element
                    models=[]
                    xpath='//div[@id="selectAnoModelomoto_chosen"]/div[@class="chosen-drop"]/ul[@class="chosen-results"]/li'
                    for model in model_element.find_elements(By.XPATH,xpath): models.append(model.text)
                except Exception as err:
                    failures_on_process.append((brand,'-',err.args[0]))
                    continue

                # looping models to retrieve desired info REVISANDO ESTA PARTE
                for model in models:
                    try:
                        # filling in brand
                        command = lambda: brand_element.click()
                        try_x_times(func=command,error_message=f'Erro ao clicar na montadora {brand} para acionar botão Pesquisar.')
                        web_element=browser.switch_to.active_element
                        web_element.send_keys(brand)
                        web_element.send_keys(Keys.ENTER)
                        time.sleep(WAIT_TIME)
                        # filling in model
                        command = lambda: model_element.click()
                        try_x_times(func=command,error_message=f'Erro ao clicar na montadora/modelo {brand}/{model} para acionar botão Pesquisar.')
                        web_element=browser.switch_to.active_element
                        web_element.send_keys(model)
                        
                        # testing if a result was found
                        # FUTURE: if it fails to find the moto by name, try by htlm li array index but first try the html li  name
                        # FUTURE: make sure there is only one result
                        if model_element.text.find('Nada encontrado com') != -1: raise RuntimeError('Modelo não encontrado.')

                        web_element.send_keys(Keys.ENTER)
                        time.sleep(WAIT_TIME)
                        # filling in 'zero km'
                        command = lambda: year_element.click()
                        try_x_times(func=command,error_message=f'Erro ao clicar no ano-modelo ds montadora {brand} antes de acionar botão Pesquisar.')
                        web_element=browser.switch_to.active_element
                        web_element.send_keys('Zero KM')
                        web_element.send_keys(Keys.ENTER)
                        time.sleep(WAIT_TIME)
                        # reading results
                        command = lambda: browser.find_element(By.ID,"buttonPesquisarmoto").click()
                        try_x_times(func=command,error_message=f'Erro ao clicar no botão Pesquisar para na montadora/modelo {brand}/{model}.')
                        for _ in range(ATTEMPTS):
                            time.sleep(WAIT_TIME * (_+1))
                            try: 
                                motorcycle_data=browser.find_element(By.ID,"resultadoConsultamotoFiltros").text.splitlines()
                                break
                            except: 
                                if _ == ATTEMPTS-1: raise RuntimeError('Dados da pesquisa não encontrados na webpage.') from None
                        if len(motorcycle_data) < 17: 
                            print(motorcycle_data)
                            raise RuntimeError('Problema nos dados da motocicleta')
                        result_file.writelines(";".join([motorcycle_data[3]]+motorcycle_data[5:11:2]+[motorcycle_data[17]])+'\n')
                        # reset search
                        try_x_times(func=click_reset_button,error_message=f'Erro ao clicar no botão Limpar Pesquisa.')
                        time.sleep(WAIT_TIME)
                    except Exception as err: 
                        failures_on_process.append((brand,model,err.args[0]))
    print('Falhas\n',failures_on_process)









from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains 

#Programa Principal

# begin: threading commands
#thread_local = threading.local()

# end: threading commands

while True:
    temp = menu('testes',['Testar conteúdo (strings) de attr "class"','Capturar Dados', 'Relatório','Threads'],1) 
    if temp == 1: testes()
    elif temp ==2: leitura_fipe()
    elif temp ==3: AbreSite()
    elif temp ==4: thd_orchestrator()
    else: break











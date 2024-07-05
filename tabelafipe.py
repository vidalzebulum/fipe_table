#! python3
# Author: Vidal Salem Zeulum
# Description
#   This module performs data extraction (zero KM motorcicles data) from FIPE website. 
#   Stability obtained using selenium 4.19
# To do
#   Check  if all Zero KM models where properly read and send warning messages
#   Improve output
#   Implement log
#   Implement Menu and browser_connection as a class 
#   Polulate README.txt
#   If necessery, try using SELECT element to avoid dicrepancies on model name

#Imports
from platform import system as osname 
from contextlib import contextmanager 
import time,datetime
from selenium import webdriver 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.support.select import Select

from vsz_log import exception_to_string #logger,log_formatter
#from vsz_funcoes_diversas import  menu 

#Constants
MODULE_NAME = 'tabelafipe'
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


def leitura_fipe():

    def click_reset_button():
        xpath='//div[@class="button pesquisa clear" and @id="buttonLimparPesquisarmoto"]'
        browser.find_element(By.XPATH,xpath).click()
    
    def check_modal():
        try:
            xpath='//div[@class="modal alert"]/div[@class="btnClose"]'
            modal_element = browser.find_element(By.XPATH,xpath)
            modal_element.click()
        except: pass
       
    def check_cloudfare(): 
        try:
            while browser.find_element(By.XPATH,'//h2[@class="h2"]').text.find('Confirme que você é humano') != -1:
                browser.find_element(By.XPATH,'//input[@type="checkbox"]').click()
                time.sleep(WAIT_TIME*6)
        except: pass

    def load_website():
        # attempt to load website without having to ask userto respond the human proof
        command = lambda: browser.get ('https://veiculos.fipe.org.br')
        for _ in range(3):
            try: try_x_times(func=command,error_message='Erro ao carregar website',repeat=1)
            except Exception as err: print(exception_to_string(err))
            check_modal()
            check_cloudfare()
        
        # acivate motorcycle panel
        command = lambda: browser.find_element(By.LINK_TEXT,"Consulta de Motos").click()
        try: try_x_times(func=command,error_message='Erro ao clicar em consulta de motos')
        except Exception as err:
            print(exception_to_string(err))
            
        try:
            xpath='//div[@class="chosen-container chosen-container-single" and @id="selectTabelaReferenciamoto_chosen"]'
            data_month = browser.find_element(By.XPATH,xpath).text
            print(data_month)
        except: pass
        
        input('Cheque se website foi carregado com sucesso e tecle enter.')
        # acivate motorcycle panel
        command = lambda: browser.find_element(By.LINK_TEXT,"Consulta de Motos").click()
        try: try_x_times(func=command,error_message='Erro ao clicar em consulta de motos')
        except Exception as err:
            print(exception_to_string(err))
            return
        command = lambda: browser.find_element(By.LINK_TEXT,"Pesquisa comum").click()
        try: try_x_times(func=command,error_message='Erro ao clicar em pesquisa comum')
        except Exception as err:
            print(exception_to_string(err))
            return

        
    with browser_connection() as browser: 
        browser.implicitly_wait(5)
        browser.maximize_window()
        load_website()

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
        failures_on_process=[] #list of tuples indicating failures on (brand,) or (brand,model)
        with open('leitura_fipe.txt','w') as result_file:
            result_file.writelines(';'.join(['hora leitura','mês consulta','código FIPE','marca',\
                                             'modelo obtido','preço','modelo desejado','observação'])+'\n')
            for brand in brands:
                check_modal()
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
                    for model in model_element.find_elements(By.XPATH,xpath): 
                        models.append((model.text,model.get_attribute('data-option-array-index')))
                except Exception as err:
                    failures_on_process.append((brand,'-',err.args[0]))
                    continue

                # looping models to retrieve desired info REVISANDO ESTA PARTE
                for model, array_index in models:
                    check_modal()
                    try:
                        # filling in brand
                        command = lambda: brand_element.click()
                        try_x_times(func=command,error_message=f'Erro ao clicar na montadora {brand} para acionar botão Pesquisar.')
                        web_element=browser.switch_to.active_element
                        web_element.send_keys(brand)
                        web_element.send_keys(Keys.ENTER)
                        time.sleep(WAIT_TIME)
                        # filling in 'zero km'
                        command = lambda: year_element.click()
                        try_x_times(func=command,error_message=f'Erro ao clicar no ano-modelo ds montadora {brand} antes de acionar botão Pesquisar.')
                        web_element=browser.switch_to.active_element
                        web_element.send_keys('Zero KM')
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
                        if model_element.text.find('Nada encontrado com') != -1: 
                            try:
                                for _ in range(len(model)): web_element.send_keys(Keys.BACKSPACE)
                                for _ in range(int(array_index)-1): web_element.send_keys(Keys.ARROW_DOWN)
                                web_element.send_keys(Keys.RETURN)
                            except Exception as err: 
                                err.args += ('Modelo não encontrado',)
                                raise RuntimeError(exception_to_string(err) ) from None
                        else: web_element.send_keys(Keys.ENTER)
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
                        obs = '--' if model == motorcycle_data[9] else 'modelo obtido diferente do modelo desejado'
                        result_file.writelines(datetime.datetime.now().strftime("%c")+";" +";".join([motorcycle_data[3]]+motorcycle_data[5:11:2]+\
                                                                                                    [motorcycle_data[17],model,obs])+'\n')
                        # reset search
                        try_x_times(func=click_reset_button,error_message=f'Erro ao clicar no botão Limpar Pesquisa.')
                        time.sleep(WAIT_TIME)
                    except Exception as err: 
                        result_file.writelines(";".join([datetime.datetime.now().strftime("%c"),'--',brand,model,exception_to_string(err) ])+'\n')
                        failures_on_process.append((brand,model,err.args[0]))
    print('Falhas\n',failures_on_process)



#Programa Principal
leitura_fipe()
""" 
while True:
    temp = menu('Leitura Tabela FIPE Motos Zero KM',['Testes','Leitura Tabela', '',''],1) 
    if temp == 1: testes()
    elif temp ==2: leitura_fipe()
    elif temp ==3: pass
    elif temp ==4: pass
    else: break
 """










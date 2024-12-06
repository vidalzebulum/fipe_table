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
import time,datetime,locale
from selenium import webdriver 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.support.select import Select
from threading import Thread, Lock, Event
from bs4 import BeautifulSoup

from vsz_log import exception_to_string,logger,log_formatter as lf
from vsz_funcoes_diversas import  menu 


#Constants
MODULE_NAME = 'tabelafipe'
WAIT_TIME  = 0.5
ATTEMPTS = 4


                       
def save_html(source):
# Receives source code from Selenium and uses  bs4 to convert
    soup = BeautifulSoup(source, "html.parser")
    with open("output.html", "w", encoding = 'utf-8') as file: 
        # prettify the soup object and convert it into a string   
        file.write(str(soup.prettify()))


@contextmanager 
def browser_connection():
# context manager to connect browser with Selenium
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


def check_modal(browser,terminate: Event, browser_lock:Lock):
    # This function deals with modal element inside FIPE website. It is meant to be called as a daemon thread.
    count= 0 #usage count
    while not terminate.is_set():
        try:
            xpath='//div[@class="modal alert"]/div[@class="btnClose"]'
            with browser_lock: browser.find_element(By.XPATH,xpath).click()
            count += 1
        except: pass
        time.sleep(WAIT_TIME)
    #logger.info(lf(function_name='check_modal',additional_messages=str(count)))
    

def check_cloudfare(browser,terminate: Event, browser_lock:Lock): 
    # This function deals with Cloudfare. It is meant to be called as a daemon thread
    count= 0 #usage count
    while not terminate.is_set():
        try:
            with browser_lock:
                if browser.find_element(By.XPATH,'//h2[@class="h2"]').text.find('Confirme que você é humano') != -1:
                    web_element=browser.switch_to.active_element
                    web_element.send_keys(Keys.TAB)
                    web_element=browser.switch_to.active_element
                    web_element.click() 
                count += 1
        except: save_html(browser.page_source)
        time.sleep(WAIT_TIME)
    #logger.info(lf(function_name='check_cloudfare',additional_messages=str(count)))


def load_website(browser,browser_lock:Lock):
    # loads Fipe website, activates motorcycle tab and checks if  content was properly loaded
    for aux1 in range(15):
        with browser_lock:
            #command = lambda: browser.get ('https://veiculos.fipe.org.br') if aux1 == 0 else browser.refresh()
            try: browser.get ('https://veiculos.fipe.org.br') if aux1 == 0 else browser.refresh() #try_x_times(func=command,error_message='Erro ao carregar website',repeat=1)
            except Exception as err: 
                #logger.error(lf(module_name='tabelafipe.py',function_name='load_website',exception=err,additional_messages='abrindo website'))
                print('erro carrragando site',exception_to_string(err))
                continue
        time.sleep(WAIT_TIME*3) # time to eliminate modal and cloudfare elements

        with browser_lock:
            #command = lambda: browser.find_element(By.LINK_TEXT,"Consulta de Motos").click()
            try: browser.find_element(By.LINK_TEXT,"Consulta de Motos").click() #try_x_times(func=command,error_message='Erro ao clicar em consulta de motos')
            except Exception as err:
                #logger.info(lf(module_name='tabelafipe.py',function_name='load_website',exception=err,additional_messages='click na aba de Consulta de Motos'))
                print('erro clicando na consulta motos',exception_to_string(err))
                continue
        time.sleep(WAIT_TIME*3) # time to eliminate modal and cloudfare elements
        
        with browser_lock:
            try:
                input('Selecione o ano desejado na tela FIPE')
                xpath='//div[@id="selectTabelaReferenciamoto_chosen"]/a[@class="chosen-single"]' #@class="chosen-container chosen-container-single" and 
                data_month = browser.find_element(By.XPATH,xpath).text
                print(data_month,"selecionado")
                if int(data_month[-4::]) <= datetime.datetime.now().year: return
            except: print(f'Erro no ano selecionado: {data_month}')
    raise RuntimeError( f'Website não carregado corretamente')

""" xpath='//div[@id="selectTabelaReferenciamoto_chosen"]'
browser.find_element(By.XPATH,xpath).click()
xpath='//div[@id="selectTabelaReferenciamoto_chosen"]/div[@class="chosen-drop"]/ul/li'
data_month = browser.find_element(By.XPATH,xpath).text
print(data_month,"elem 1")
xpath='//div[@id="selectTabelaReferenciamoto_chosen"]/div[@class="chosen-drop"]/ul/li[@class="active-result"]'
data_month = browser.find_element(By.XPATH,xpath).text
print(data_month,"elem 3")
xpath='//div[@id="selectTabelaReferenciamoto_chosen"]'
browser.find_element(By.XPATH,xpath).click() """            


def get_data(browser,browser_lock: Lock):

    def click_reset_button():
        xpath='//div[@class="button pesquisa clear" and @id="buttonLimparPesquisarmoto"]'
        browser.find_element(By.XPATH,xpath).click()

    with browser_lock:
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
            time.sleep(3* WAIT_TIME)
            with browser_lock:
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
                time.sleep(2*WAIT_TIME)
                with browser_lock:
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
while True: 
    temp = menu('Leitura Tabela FIPE Motos Zero KM',['Leitura Tabela','Testes', '',''],1) 
    if temp ==1: 
        with browser_connection() as browser: 
            browser.implicitly_wait(2)
            terminate_background = Event() # signal to stop backgroud process
            browser_lock = Lock()
            browser.maximize_window()
            modal_thread = Thread(target=check_modal, name='FipeCheckModal', daemon=True, args=(browser,terminate_background,browser_lock))
            modal_thread.start()
            cloudfare_thread = Thread(target=check_cloudfare, name='FipeCloudfare', daemon=True, args=(browser,terminate_background,browser_lock))
            cloudfare_thread.start()
            try:
                load_website(browser,browser_lock)
                get_data(browser,browser_lock)
            #terminate_background(terminate_modal)
            except Exception as err:
                print(err)

            terminate_background.set()
            modal_thread.join()
            cloudfare_thread.join()
    elif temp in(2,3,4) : pass
    else: break











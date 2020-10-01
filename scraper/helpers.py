from selenium import webdriver
import time


def create_headless_browser():
    # options = Options()
    # options.set_headless()
    # assert options.headless  # assert Operating in headless mode
    # return webdriver.Chrome(options=options)
    return webdriver.Chrome()


def load_full_page(browser, page_url):
    browser.get(page_url)
    time.sleep(5)
    print(f"@@@ {page_url} is loaded @@@")
    return browser.page_source

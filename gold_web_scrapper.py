import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from xlrd import open_workbook


def get_all():
    df = pd.concat([
        get_apmex(),
        get_money_metals(),
        get_goldeneagle(),
        get_jmbullion(),
        get_ebay(),
        get_bgasc(),
    ], ignore_index=True)

    df['tv'] = np.where(df['source'].isin(['ebay']), 0.99, 1) * df['price']
    df.sort_values('tv', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


##############################################################################################################


def get_apmex():
    req = requests.get('https://www.apmex.com/category/15000/gold-coins/all?vt=g&f_metalname=gold&f_bulliontype=coin&f_productoz=1+oz&f_mintyear=random&sortby=priceasc')

    soup = BeautifulSoup(req.text, 'lxml')

    divs = soup.find_all('div')

    cards = []
    for i in divs:
        class_name = i.get('class')
        if class_name!=None and 'mod-product-card' in class_name:
            cards.append(i)

    df = pd.DataFrame(
        [(card.find_next(attrs={'class': 'price'}).text,
        card.find_next(attrs={'class': 'mod-product-title'}).text.strip(),
         'https://apmex.com'+card.find_next('a', attrs={'class': 'item-link'}).attrs['href']
         )
        for card in cards],
        columns=['price','title', 'url']
    )
    df= df[~df['price'].str.contains('Alert')]
    df = df[~df['title'].str.contains('Commemorative')]
    df['price'] = pd.to_numeric(df['price'].str.replace('$','').str.replace(',',''), errors='ignore')
    df['source'] = 'apmex'
    return df

def get_money_metals():
    url = 'https://www.moneymetals.com/buy/gold/coins'
    req = requests.get(url)
    soup =  BeautifulSoup(req.text, 'lxml')

    divs = soup.find_all('div')

    cards=  []
    for i in divs:
        class_name = i.get('class')
        if class_name != None and 'mmx-product-thumb' in class_name:
            cards.append(i)

    df = pd.DataFrame(
        [(
        i.find_next('p').text.split('As low as: ')[-1],
        i.find_next(attrs={'class': 'mmx-product-title'}).text.strip(),
        i.find_next('a').attrs['href']
    ) for i in cards],
        columns=['price','title', 'url']
    )

    df = df[~df['price'].str.contains('View')]
    df = df[df['title'].str.contains('1 Oz')]
    df['source'] = 'moneymetals'
    df['price'] = pd.to_numeric(df['price'].str.replace('$','').str.replace(',',''))
    return df

def _inner_link_goldeneagle(l):
    req = requests.get(l)
    soup = BeautifulSoup(req.text, 'lxml')
    prods_list = soup.find_all(attrs={'class': 'prods-list'})
    
    if len(prods_list)>0:
        prods_list = prods_list[0]
    
        one_ounce_url = [
            'https://www.goldeneaglecoin.com'+i.attrs['href'] for i in prods_list.find_all('a') 
            if 'href' in i.attrs and 'one-ounce' in i.attrs['href']]

        if one_ounce_url == []:
            one_ounce_url = [
            'https://www.goldeneaglecoin.com'+i.attrs['href'] for i in prods_list.find_all('a') 
            if 'href' in i.attrs][0]

        else:
            one_ounce_url = one_ounce_url[0]

        req = requests.get(one_ounce_url)
        soup = BeautifulSoup(req.text, 'lxml')
        
    prods_list = soup.find_all(attrs={'class': 'product-list'})[0]
    list_items = prods_list.find_all('li')

    in_stock_items = [(
            i.find_next(attrs={'itemprop': 'price'}).text,
            i.find_next(attrs={'itemprop': 'url'}).text,
            'https://www.goldeneaglecoin.com'+i.find_next('a').attrs['href']
        )
        for i in list_items if
        i.find_next(attrs={'class': 'instock'}) != None and
        'Available' in i.find_next(attrs={'class': 'instock'}).text.strip()
        and len(i.find_all(attrs={'class': 'outofstock'}))==0
    ]

    df = pd.DataFrame(in_stock_items, columns=['price','title','url'])
    return df

def get_goldeneagle():
    url = 'https://www.goldeneaglecoin.com/buy-gold'
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'lxml')
    prods_list = soup.find_all(attrs={'class': 'prods-list'})[0]
    links = ['https://www.goldeneaglecoin.com'+i.attrs['href'] for i in prods_list.find_all('a')]

    df = pd.concat([_inner_link_goldeneagle(l) for l in links], ignore_index=True)

    df['price'] = pd.to_numeric(df['price'].str.replace('$','').str.replace(',',''))
    df.sort_values('price', inplace=True)

    df = df[
        ~df['title'].str.lower().str.contains('silver')&\
        df['title'].str.lower().str.contains(' 1 oz')
    ].reset_index(drop=True)

    df['source'] = 'goldeneaglecoin'
    return df

def _scrape_jmbullion(l):
    
    soup = BeautifulSoup(requests.get(l).text, 'lxml')
    prod_section = [i.find_next('a').attrs['href'] for i in soup.find_all(attrs={'class': 'prod-section'})]
    prod_section = [i if 'jmbullion' in i else 'https://www.jmbullion.com'+i  for i in prod_section ]
    
    if len(prod_section) == 0:
        tab1 = soup.find_all(id='tab1')
        #print(tab1)
        if len(tab1)>0:
            tab1=tab1[0]
            sub_links = tab1.find_all('a')
            sub_links = [i.attrs['href'] for i in sub_links if 'href' in i.attrs]
            sub_links = [i if 'jmbullion' in i else 'https://www.jmbullion.com'+i  for i in sub_links ]
            return sub_links
            
        else:
            print('ERROR')
            print(l)
    
    links=[]
    for i in prod_section:
        if len(i.split('/'))>4:
            links.extend(_scrape_jmbullion(i))
        else:
            links.append(i)
            
    return links

def _jbullion_scrape_one(l):
    try:
        soup = BeautifulSoup(requests.get(l).text, 'lxml')
        title = soup.find_all(attrs={'class':'title-area'})[0].text.strip()
        payment_inner = soup.find_all(attrs={'class': 'payment-inner'})[0]
        payment_tbl = payment_inner.find_all('tbody')
        payment_tbl = [i for i in payment_tbl if '$' in i.text][0]
        
        price = min([float(i.text.strip().replace('$','').replace(',','')) for i in payment_tbl.find_all('td') if '$' in i.text])
        in_stock = 'in stock' in [i.text.strip().lower() for i in soup.find_all(attrs={'class': 'title'})]

        if in_stock:
            return (price, title, l)
        else:
            return (None,None,None)
    except:
        
        return (None, None, None)

def get_jmbullion():
    url = 'https://www.jmbullion.com/gold/'
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'lxml')
    prod_selection = soup.find_all(attrs={'class': 'prod-section'})
    links = [i.find_next('a').attrs['href'] for i in prod_selection 
     if 'coin' in i.find_next('a').attrs['href'] or 
    'sovereign' in i.find_next('a').attrs['href']]
    links = [i if 'https://www.jmbullion.com' in i else 'https://www.jmbullion.com' +i for i in links]

    link_list = []
    for l in links:
        l2 = _scrape_jmbullion(l)
        if len(l2)>0:
            link_list.extend(l2)
        else:
            print('ERROR')
            print(l)

    one_ounce_links= [i for i in link_list if '1-oz' in i.lower() and 'round' not in i.lower()]

    df = pd.DataFrame(
        [_jbullion_scrape_one(i) for i in one_ounce_links],
        columns=['price', 'title','url']
    )

    df['source'] = 'jmbullion'

    df.dropna(inplace=True)
    return df

def get_ebay():
    url = 'https://www.ebay.com/sch/i.html?_from=R40&_nkw=gold+coins&_sacat=39482&Precious%2520Metal%2520Content%2520per%2520Unit=1%2520oz&_dcat=177652&LH_BIN=1&_sop=12&_ipg=200'
    soup = BeautifulSoup(requests.get(url).text, 'lxml')

    count = 0
    listings=[]
    while count<500:
        count += 1

        listing = soup.find_all(
            id='srp-river-results-listing{}'.format(count)
        )

        if listing == []: 
            break
        else:
            listing = listing[0]
            price = float(listing.find_next(
                attrs={'class': 's-item__price'}
            ).text.replace('$','').replace(',',''))

            url = listing.find_next('a',
                attrs={'class': 's-item__link'}
            ).attrs['href']

            title = listing.find_next(
                attrs={'class': 's-item__title'}
            ).text
            listings.append((price,title,url))
    
    df = pd.DataFrame(listings, columns=['price','title','url'])
    
    df = df[
        df['title'].str.lower().str.contains('1 oz')|\
        df['title'].str.lower().str.contains('1oz')|\
        df['title'].str.lower().str.contains('1 ounce')
    ]
    
    df.sort_values('price', inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['source'] = 'ebay'

    return df

def _get_bgasc(url):
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    price = float([i.text.strip() for i in soup.find_all('div', attrs={'class': 'price'}) if 'As Low As' in i.text.strip() ][0].split(
    'As Low As:')[-1].strip().replace('$','').replace(',',''))
    title = soup.find_all('div', id='breadcrumb')[0].find_all('a')[-1].text
    return (price, title, url, 'bgasc')

def get_bgasc():

    url_list = [
        'https://www.bgasc.com/product/1-oz-gold-american-eagle-coin-brilliant-uncirculated-gem-bullion-random-year/gold-eagles-1-oz',
        'https://www.bgasc.com/product/50-1-oz-american-gold-buffalo-bu-gem-9999-fine-24kt-gold-year-our-choice-g_buf_rndm_1_oz_raw/gold-buffalo-coins-and-sets',
        'https://www.bgasc.com/product/canadian-gold-maple-leaf-dates-our-choice-brilliant-uncirculated-gem-9999-fine/canadian-gold-maple-leafs-other-canadian-gold-coins',
        'https://www.bgasc.com/product/1-oz-south-african-gold-krugerrand-bullion-brilliant-uncirculated-gem-year-our-choice/south-african-gold-krugerrands',
        'https://www.bgasc.com/product/australia-1-oz-gold-kangaroo-nugget-bu-coin-random-year/australian-gold-kangaroos-nuggets',
        'https://www.bgasc.com/product/1-oz-brilliant-uncirculated-gold-austrian-philharmonic-in-a-year-of-our-choice/austrian-gold-coins-philharmonics-more',
        'https://www.bgasc.com/product/1-oz-gold-britannia-bullion-coin-bu-random-year/british-gold-sovereigns-gold-britannias',
        'https://www.bgasc.com/product/mexico-gold-50-pesos-agw-1-2057-oz-random-year/mexican-gold-coins',
    ]

    return pd.DataFrame([_get_bgasc(url) for url in url_list], columns=['price','title','url', 'source'])


##############################################################################################################


def main():
    df = get_all()
    file_name = "gold_output.xlsx"
    df.to_excel(file_name)
    book = open_workbook(file_name,on_demand=True)
    print("COMPLETE")



if __name__ == "__main__": 
    main()

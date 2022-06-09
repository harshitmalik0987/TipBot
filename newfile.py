#-*- coding: utf-8 -*-

from requests import Request, Session
import requests
import json
import codecs
import requests
from bs4 import BeautifulSoup, SoupStrainer
import re
import subprocess
from telegram.ext.dispatcher import run_async
from telegram.ext import Updater
from html import escape
from tronapi import Tron


full_node = 'https://api.trongrid.io'
solidity_node = 'https://api.trongrid.io'
event_server = 'https://api.trongrid.io'

PK = "a9795907f31f554934efdf35383973e87e501ef333bf71b87c11cbf2b469c504"

tron = Tron(full_node=full_node,
    solidity_node=solidity_node,
    event_server=event_server)

def checkTrc10(s, base=10, val=None):
    try:
        return int(s, base)
    except ValueError:
        return val

def setTronPK(pk):
    tron.private_key = pk
    tron.default_address = tron.address.from_private_key(pk).base58

setTronPK(PK)


updater = Updater(token='5464645214:AAFeBrA2M7-b8cJinfh3gbcmI2h5PHIQetw')
dispatcher = updater.dispatcher

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                    level=logging.INFO)



def start(update, context):
    user = update.message.from_user.username
    update.effective_message.reply_text("🔥 Welcome to Artificial TronAPI Bot\n\n🔝 Use /help to See the Available Command....",)

def help(update, context):
    update.effective_message.reply_text(text="The following commands are at your disposal:\n/start\n/help [available command]\n/balance [address]\n/details [transaction hash]\n/price [token]\n/convert [amount] [token1] [token2]")


def balance(update, context):
    target = update.message.text[9:]
    print(target)
    target =  target.split(" ")[0]
    url = "https://apilist.tronscan.org/api/account"
    payload = {
        "address": target,
    }
    res = requests.get(url, params=payload)
    try:
        trc20token_balances = json.loads(res.text)["balances"]
    except KeyError:
        update.effective_message.reply_text("Wrong Address or Wrong Format\n/balance [address]")
        return
    aaa =""
    if trc20token_balances == None:
        update.effective_message.reply_text("0")
    else:
        aaa += "Tron(TRX) - "
        for item in trc20token_balances:
            if item["tokenName"] == "trx":
                aaa += str(float(int(item["balance"])/(10**item["tokenDecimal"]))) + "\n\nOther Tokens - \n"
                pass
            else:
                aaa += item["tokenName"]+"("+item["tokenAbbr"]+") - "+str(float(int(item["balance"])/(10**item["tokenDecimal"])))+"\n"
        update.effective_message.reply_text("<code>"+aaa+"</code>", parse_mode="html")


def send(update, context):
    user = update.message.from_user.username
    if user != "kratos_71" and user != "tron_apibot" :
            update.effective_message.reply_text(text="You are not the Master - @NobitaNobi_420!!!\nGo create your own bot....")
    else:
        target = update.message.text[6:]
        try:
            amount =  target.split(" ")[1]
            token = target.split(" ")[2]
            target =  target.split(" ")[0]
        except IndexError:
            update.effective_message.reply_text("Wrong format!\n`/send [address] [amount] [TokenName]`",parse_mode="markdown")
            return
        print(target)
        
        if len(target) == 34:
            url = "https://apilist.tronscan.org/api/account"
            payload = {
                "address": tron.address.from_private_key(PK)["base58"],
            }
            res = requests.get(url, params=payload)
            trc20token_balances = json.loads(res.text)["balances"]
            if token.upper() == "TRX":
                for item in trc20token_balances:
                    if item["tokenName"] == "trx":
                        if (float(item["balance"])/(10**item["tokenDecimal"])) < float(amount):
                            update.effective_message.reply_text("Insufficient Balance in account...")
                        else:
                            amount = float(amount)
                            txn = tron.trx.send(target, amount)
                            update.effective_message.reply_text(text="@{0} sent <code>{1}</code> {2} TRX\nTXN ID - https://tronscan.org/#/transaction/{3}".format(user, target, amount, txn["transaction"]["txID"]),parse_mode="html")
            
            else:
                for item in trc20token_balances:
                    if str(item["tokenName"]).upper() == str(token).upper() or str(item["tokenAbbr"]).upper() == str(token).upper():
                        print(int(float(amount)*(10**item["tokenDecimal"])))
                        if item["tokenType"] == "trc10":
                            try:
                                txn = tron.trx.send_token(target, int(float(amount)*(10**item["tokenDecimal"])), int((item["tokenId"])))
                                update.effective_message.reply_text(text="@{0} sent <code>{1}</code> <code>{2}</code> {3}\nTXN ID - https://tronscan.org/#/transaction/{4}".format(user, target, amount, token, txn["transaction"]["txID"]),parse_mode="html",disable_web_page_preview=True)
                            except Exception as inst:
                                print(f'\t\tError: {inst}') 
                                update.effective_message.reply_text(f'\t\tFail to send <code>{target}</code> <code>{amount}</code> <code>{token}</code>',parse_mode="html")
                            return
                            
                        elif item["tokenType"] == "trc10":
                            
                            print("hi")
                            print(int(float(amount)*(10**item["tokenDecimal"])))
                            try:
                                txn = tron.transaction_builder.trigger_smart_contract(
                                    contract_address=tron.address.to_hex(str(item["tokenId"])),
                                    function_selector='transfer(address,uint256)',
                                    fee_limit=10000000,
                                    call_value=0,
                                    parameters=[
                                        {'type': 'address', 'value': tron.address.to_hex(target)},
                                        {'type': 'int256', 'value': int(float(amount)*(10**item["tokenDecimal"]))}
                                    ]
                                )
                                update.effective_message.reply_text(text="@{0} sending <code>{1}</code> <code>{2}</code> {3}\nTXN ID - https://tronscan.org/#/transaction/{4}".format(user, target, amount, token, txn["transaction"]["txID"]),parse_mode="html",disable_web_page_preview=True)
                                txResult = tron.trx.sign_and_broadcast(txn['transaction'])
                                if (not txResult['result']):
                                    raise Exception('Transfer fail...')
                            except Exception as inst:
                                print(f'\t\tError: {inst}')                                  
                                update.effective_message.reply_text(f'\t\tFailed to send {target} {amount} {token}')
                            return
                else:
                    url = "https://apilist.tronscan.org/api/account"
                    payload = {
                        "address": tron.address.from_private_key(PK)["base58"],
                    }
                    res = requests.get(url, params=payload)
                    trc20token_balances = json.loads(res.text)["trc20token_balances"]
                    for item in trc20token_balances:
                        if str(item["tokenName"]).upper() == str(token).upper() or str(item["tokenAbbr"]).upper() == str(token).upper():
                            if (float(item["balance"])/(10**item["tokenDecimal"])) < float(amount):
                                update.effective_message.reply_text("Insufficient Balance in account...")
                            else:
                                try:
                                    txn = tron.transaction_builder.trigger_smart_contract(
                                        contract_address=tron.address.to_hex(str(item["tokenId"])),
                                        function_selector='transfer(address,uint256)',
                                        fee_limit=10000000,
                                        call_value=0,
                                        parameters=[
                                            {'type': 'address', 'value': tron.address.to_hex(target)},
                                            {'type': 'int256', 'value': int(float(amount)*(10**item["tokenDecimal"]))}
                                        ]
                                    )
                                    update.effective_message.reply_text(text="@{0} sending <code>{1}</code> <code>{2}</code> {3}\nTXN ID - https://tronscan.org/#/transaction/{4}".format(user, target, amount, token, txn["transaction"]["txID"]),parse_mode="html",disable_web_page_preview=True)
                                    txResult = tron.trx.sign_and_broadcast(txn['transaction'])
                                    if (not txResult['result']):
                                        raise Exception('Transfer fail...')
                                except Exception as inst:
                                    print(f'\t\tError: {inst}')                                  
                                    update.effective_message.reply_text(f'\t\tFailed to send {target} {amount} {token}')
        else:
            update.effective_message.reply_text(text="Error Wrong Trx Address")


def details(update, context):
    user = update.message.from_user.username
    target = update.message.text[9:]
    print(target)
    target =  target.split(" ")[0]
    url = "https://apilist.tronscan.org/api/transaction-info"
    payload = {
        "hash": target,
    }
    res = requests.get(url, params=payload)
    try:
        item = json.loads(res.text)["contractData"]
    except KeyError:
        update.effective_message.reply_text("Wrong Hash")
        return
    aaa =""
    if item == None:
        update.effective_message.reply_text("0")
    else:
        try:
            aaa += "From - <code>"+item["owner_address"]+"</code>\nTo - <code>"+item["to_address"]+"</code>\n"
            aaa += "Transfer Type - <code>TRC10 Transfer</code>\n"
            aaa += "Token name - <code>"+item["tokenInfo"]["tokenName"]+"</code>\nToken Symbol - <code>"+item["tokenInfo"]["tokenAbbr"]+"</code>\n"
            aaa += "Amount - <code>" + str(int(item["amount"])/10**(item["tokenInfo"]["tokenDecimal"])) + "</code>\n\n"
            aaa += "Link of transaction on Tronscan - \n                                <a href = \"https://tronscan.org/#/transaction/"+target+"\">Click Here</a>"
            update.effective_message.reply_text(aaa, parse_mode="html", disable_web_page_preview=True)
        except KeyError:
            aaa =""
            try:
                item = json.loads(res.text)["trc20TransferInfo"][0]
                if item == None:
                    update.effective_message.reply_text("0")
                else:
                    aaa += "From - <code>"+item["from_address"]+"</code>\nTo - <code>"+item["to_address"]+"</code>\n"
                    aaa += "Transfer Type - <code>TRC20 Transfer</code>\n"
                    aaa += "Token name - <code>"+item["name"]+"</code>\nToken Symbol - <code>"+item["symbol"]+"</code>\n"
                    aaa += "Amount - <code>" + str(int(item["amount_str"])/10**(item["decimals"])) + "</code>\n\n"
                    aaa += "Link of transaction on Tronscan - \n                                <a href = \"https://tronscan.org/#/transaction/"+target+"\">Click Here</a>"
                    update.effective_message.reply_text(aaa, parse_mode="html", disable_web_page_preview=True)
            except KeyError:
                aaa = ""
                item = json.loads(res.text)["contractData"]
                if item == None:
                    update.effective_message.reply_text("0")
                else:
                    try:
                        aaa += "From - <code>"+item["owner_address"]+"</code>\nTo - <code>"+item["to_address"]+"</code>\n"
                        aaa += "Transfer Type - <code>TRX Transfer</code>\n"
                        aaa += "Token name - <code>Tron</code>\nToken Symbol - <code>TRX</code>\n"
                        aaa += "Amount - <code>" + str(int(item["amount"])/10**6) + "</code>\n\n"
                        aaa += "Link of transaction on Tronscan - \n                                <a href = \"https://tronscan.org/#/transaction/"+target+"\">Click Here</a>"
                        update.effective_message.reply_text(aaa, parse_mode="html", disable_web_page_preview=True)
                    except KeyError:
                        update.effective_message.reply_text("Wrong Hash")



def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)




from telegram.ext import CommandHandler

caps_handler = CommandHandler('caps', caps)
dispatcher.add_handler(caps_handler)

details_handler = CommandHandler('details', details)
dispatcher.add_handler(details_handler)

send_handler = CommandHandler('send', send)
dispatcher.add_handler(send_handler)

balance_handler = CommandHandler('balance', balance)
dispatcher.add_handler(balance_handler)

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)

updater.start_polling()
def convert(update, context):
    abab = update.message.text[9:]
    amount =  abab.split(" ")[0]
    token1 =  abab.split(" ")[1]
    try:
        token2 = abab.split(" ")[2]
    except IndexError:
        amount = 1
        token1 =  abab.split(" ")[0]
        token2 =  abab.split(" ")[1]
    url = 'https://pro-api.coinmarketcap.com/v1/tools/price-conversion'
    parameters = {
    'amount' : amount,
    'symbol' : token1.upper(),
    'convert' : token2.upper()
    }
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': 'bfb8762c-dee0-44fb-8703-2bb5ae64f7cc',
    }

    session = Session()
    session.headers.update(headers)
    response = session.get(url, params=parameters)
    data = json.loads(response.text)
    converted = format(float(str(round(data['data']['quote'][token2.upper()]['price'], 5))), 'f')
    #res = requests.get(url, params=payload)
    #item = json.loads(res.text)
    update.effective_message.reply_text(""+str(amount) + " " + token1.upper() + " = " + str(converted) + " " + token2.upper()+"")


def price(update, context):
    abab = update.message.text[7:]
    #try:
    token =  abab.split(" ")[0]

    if token == '':
        token = "BTC"
    aaa = ""
    url = 'https://pro-api.coinmarketcap.com/v1/tools/price-conversion'
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': 'bfb8762c-dee0-44fb-8703-2bb5ae64f7cc',
    }
    session = Session()
    session.headers.update(headers)
    parameters = {
    'amount' : 1,
    'symbol' : token.upper(),
    'convert' : "USD"
    }
    
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        pricee = format(float(str(round(data['data']['quote']['USD']['price'], 5))), 'f')
        aaa += (token.upper() + "= $" + str(pricee) + " | ")
    except:
        return 'Currency Not Found!'
    session = Session()
    session.headers.update(headers)
    parameters = {
    'amount' : 1,
    'symbol' : token.upper(),
    'convert' : "BTC"
    }
    
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        pricee = format(float(str(round(data['data']['quote']['BTC']['price'], 5))), 'f')
        aaa += str(pricee) + "₿\n"
    except:
        #print(e)
        return 'Currency Not Found!'
    session = Session()
    session.headers.update(headers)
    parameters = {
    'amount' : 1,
    'symbol' : token.upper(),
    'convert' : "ETH"
    }
    
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        pricee = format(float(str(round(data['data']['quote']['ETH']['price'], 5))), 'f')
        aaa += str(pricee) + "Ξ"
    except:
        #print(e)
        update.message.reply_text('Currency Not Found!')
    update.effective_message.reply_text("<code>"+aaa+"</code>", parse_mode="html")


price_handler = CommandHandler('price', price)
dispatcher.add_handler(price_handler)

convert_handler = CommandHandler('convert', convert)
dispatcher.add_handler(convert_handler)

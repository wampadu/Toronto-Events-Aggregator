import os
import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import calendar
import html
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# === Proxy List ===
PROXY_LIST = [
    "http://45.8.211.187:80",
    "http://45.67.215.97:80",
    "http://141.101.113.121:80",
    "http://102.177.176.54:80",
    "http://69.84.182.26:80",
    "http://170.114.46.143:80",
    "http://141.101.113.21:80",
    "http://170.114.45.116:80",
    "http://45.67.215.232:80",
    "http://216.205.52.186:80",
    "http://45.67.215.127:80",
    "http://45.67.215.95:80",
    "http://185.221.160.6:80",
    "http://69.84.182.123:80",
    "http://185.238.228.166:80",
    "http://170.114.46.124:80",
    "http://141.101.120.254:80",
    "http://102.177.176.67:80",
    "http://69.84.182.175:80",
    "http://170.114.45.3:80",
    "http://216.205.52.151:80",
    "http://170.114.45.138:80",
    "http://170.114.46.117:80",
    "http://170.114.45.153:80",
    "http://45.67.215.168:80",
    "http://45.8.211.225:80",
    "http://89.116.250.43:80",
    "http://185.238.228.110:80",
    "http://89.116.250.220:80",
    "http://216.205.52.193:80",
    "http://45.67.215.187:80",
    "http://185.238.228.116:80",
    "http://45.67.215.252:80",
    "http://170.114.45.31:80",
    "http://45.67.215.89:80",
    "http://69.84.182.242:80",
    "http://141.101.113.101:80",
    "http://89.116.250.174:80",
    "http://108.162.198.211:80",
    "http://102.177.176.252:80",
    "http://69.84.182.144:80",
    "http://45.8.211.136:80",
    "http://69.84.182.21:80",
    "http://89.116.250.142:80",
    "http://45.67.215.188:80",
    "http://141.101.120.218:80",
    "http://45.8.211.151:80",
    "http://102.177.176.249:80",
    "http://185.221.160.106:80",
    "http://45.67.215.87:80",
    "http://8.35.211.27:80",
    "http://102.177.176.190:80",
    "http://89.116.250.253:80",
    "http://102.177.176.202:80",
    "http://216.205.52.209:80",
    "socks4://8.213.195.191:80",
    "http://91.193.58.111:80",
    "http://170.114.45.86:80",
    "http://185.221.160.222:80",
    "socks4://117.211.160.52:55443",
    "http://141.101.120.151:80",
    "http://69.84.182.133:80",
    "http://102.177.176.188:80",
    "http://89.116.250.235:80",
    "http://45.8.211.100:80",
    "http://216.205.52.183:80",
    "http://102.177.176.43:80",
    "http://170.114.46.13:80",
    "http://45.8.211.19:80",
    "http://108.162.192.249:80",
    "http://108.162.198.28:80",
    "http://170.114.46.142:80",
    "http://103.160.204.146:80",
    "http://89.116.250.175:80",
    "http://141.101.120.169:80",
    "http://102.177.176.37:80",
    "http://216.205.52.241:80",
    "http://102.177.176.181:80",
    "http://216.205.52.227:80",
    "http://185.221.160.145:80",
    "http://102.177.176.155:80",
    "http://141.101.120.198:80",
    "http://185.238.228.150:80",
    "http://69.84.182.9:80",
    "http://216.24.57.192:80",
    "http://45.67.215.191:80",
    "http://102.177.176.95:80",
    "http://216.205.52.139:80",
    "http://170.114.46.157:80",
    "http://185.238.228.181:80",
    "http://185.221.160.83:80",
    "http://170.114.46.118:80",
    "http://8.35.211.182:80",
    "http://185.221.160.107:80",
    "http://216.205.52.251:80",
    "http://108.162.193.60:80",
    "http://185.221.160.253:80",
    "http://69.84.182.12:80",
    "http://108.162.195.130:80",
    "http://108.162.195.155:80",
    "http://216.205.52.134:80",
    "http://216.205.52.68:80",
    "http://102.177.176.17:80",
    "http://141.101.120.150:80",
    "http://185.238.228.11:80",
    "http://216.205.52.154:80",
    "http://141.101.120.175:80",
    "http://216.205.52.157:80",
    "http://216.205.52.128:80",
    "http://89.116.250.146:80",
    "http://216.205.52.113:80",
    "http://69.84.182.202:80",
    "http://170.114.45.134:80",
    "http://89.116.250.27:80",
    "http://45.67.215.30:80",
    "http://185.221.160.185:80",
    "http://89.116.250.128:80",
    "http://185.238.228.17:80",
    "http://216.205.52.51:80",
    "http://185.238.228.139:80",
    "http://170.114.45.233:80",
    "http://216.205.52.239:80",
    "http://108.162.192.36:80",
    "http://102.177.176.218:80",
    "http://45.67.215.34:80",
    "http://102.177.176.219:80",
    "http://45.8.211.213:80",
    "http://141.101.120.153:80",
    "http://216.205.52.202:80",
    "http://216.205.52.214:80",
    "http://102.177.176.139:80",
    "http://185.221.160.75:80",
    "http://170.114.45.24:80",
    "http://185.221.160.182:80",
    "http://141.101.120.19:80",
    "http://216.205.52.211:80",
    "http://69.84.182.134:80",
    "http://69.84.182.91:80",
    "http://69.84.182.176:80",
    "http://141.101.120.224:80",
    "http://102.177.176.8:80",
    "http://102.177.176.129:80",
    "http://216.205.52.2:80",
    "http://141.101.115.249:80",
    "http://45.67.215.204:80",
    "http://170.114.45.125:80",
    "http://102.177.176.194:80",
    "http://141.101.120.160:80",
    "http://185.238.228.114:80",
    "http://45.67.215.86:80",
    "http://102.177.176.225:80",
    "http://141.101.120.120:80",
    "http://89.116.250.19:80",
    "http://170.114.46.137:80",
    "http://69.84.182.150:80",
    "http://69.84.182.241:80",
    "http://103.156.75.132:8181",
    "http://141.101.120.173:80",
    "http://170.114.45.137:80",
    "http://141.101.120.176:80",
    "http://108.162.193.78:80",
    "http://89.116.250.232:80",
    "http://89.116.250.83:80",
    "http://216.205.52.164:80",
    "http://69.84.182.61:80",
    "http://108.162.195.56:80",
    "http://103.126.87.155:8081",
    "http://108.162.193.102:80",
    "socks4://14.232.166.150:5678",
    "http://102.177.176.68:80",
    "http://216.205.52.34:80",
    "http://108.162.193.79:80",
    "socks4://135.148.9.18:25117",
    "http://216.205.52.240:80",
    "http://185.221.160.158:80",
    "http://170.114.46.185:80",
    "http://141.101.120.18:80",
    "http://141.101.120.107:80",
    "http://69.84.182.213:80",
    "http://141.101.120.174:80",
    "http://89.116.250.255:80",
    "http://185.221.160.121:80",
    "http://185.221.160.118:80",
    "http://141.101.120.217:80",
    "http://185.221.160.29:80",
    "http://102.177.176.10:80",
    "http://185.238.228.14:80",
    "http://185.221.160.239:80",
    "http://69.84.182.167:80",
    "http://69.84.182.35:80",
    "http://89.116.250.162:80",
    "http://216.205.52.76:80",
    "http://45.8.211.102:80",
    "http://141.101.120.216:80",
    "http://45.67.215.240:80",
    "http://45.8.211.110:80",
    "http://185.221.160.166:80",
    "http://45.67.215.249:80",
    "http://170.114.45.131:80",
    "http://216.205.52.220:80",
    "http://216.205.52.208:80",
    "http://185.221.160.123:80",
    "http://102.177.176.180:80",
    "http://141.101.120.162:80",
    "http://45.8.211.184:80",
    "http://108.162.195.131:80",
    "http://170.114.45.103:80",
    "http://69.84.182.205:80",
    "http://69.84.182.168:80",
    "http://108.162.198.162:80",
    "http://89.116.250.17:80",
    "http://185.221.160.36:80",
    "http://45.67.215.231:80",
    "http://102.177.176.31:80",
    "http://108.162.198.141:80",
    "http://170.114.45.10:80",
    "http://69.84.182.32:80",
    "http://103.160.204.77:80",
    "http://216.205.52.243:80",
    "http://141.101.114.44:80",
    "socks4://75.2.1.177:8080",
    "http://141.101.120.101:80",
    "http://108.162.193.94:80",
    "http://89.116.250.134:80",
    "http://69.84.182.181:80",
    "http://216.205.52.194:80",
    "http://216.205.52.100:80",
    "http://185.221.160.218:80",
    "http://89.116.250.217:80",
    "http://69.84.182.55:80",
    "http://45.67.215.220:80",
    "http://108.162.194.77:80",
    "http://216.205.52.121:80",
    "http://89.116.250.238:80",
    "http://69.84.182.46:80",
    "http://185.221.160.48:80",
    "http://69.84.182.221:80",
    "http://170.114.45.46:80",
    "http://45.67.215.14:80",
    "http://108.162.193.185:80",
    "http://45.67.215.33:80",
    "http://141.101.113.189:80",
    "http://103.116.7.132:80",
    "http://108.162.192.173:80",
    "http://185.221.160.32:80",
    "http://141.101.115.4:80",
    "http://69.84.182.56:80",
    "http://45.67.215.93:80",
    "http://45.67.215.58:80",
    "http://89.116.250.56:80",
    "http://185.238.228.146:80",
    "http://141.101.120.171:80",
    "http://185.221.160.21:80",
    "http://170.114.45.85:80",
    "http://170.114.45.96:80",
    "http://102.177.176.6:80",
    "http://170.114.46.17:80",
    "http://89.116.250.241:80",
    "http://141.101.114.26:80",
    "http://45.67.215.54:80",
    "http://170.114.45.188:80",
    "http://89.116.250.101:80",
    "http://170.114.46.161:80",
    "http://108.162.193.191:80",
    "http://102.177.176.167:80",
    "http://216.205.52.23:80",
    "http://216.24.57.140:80",
    "http://216.205.52.228:80",
    "http://185.221.160.59:80",
    "http://170.114.46.131:80",
    "http://216.205.52.67:80",
    "http://170.114.45.8:80",
    "http://185.221.160.251:80",
    "http://89.116.250.85:80",
    "http://102.177.176.32:80",
    "http://170.114.45.238:80",
    "http://170.114.45.215:80",
    "http://108.162.196.71:80",
    "http://103.155.168.168:8299",
    "http://45.67.215.211:80",
    "http://216.205.52.45:80",
    "http://45.67.215.94:80",
    "http://117.161.170.163:9449",
    "http://69.84.182.130:80",
    "http://102.177.176.196:80",
    "http://141.101.115.26:80",
    "http://185.221.160.212:80",
    "http://89.116.250.6:80",
    "http://89.116.250.139:80",
    "http://8.6.112.6:80",
    "http://45.8.211.1:80",
    "http://45.8.211.122:80",
    "http://69.84.182.107:80",
    "http://89.116.250.144:80",
    "http://216.205.52.86:80",
    "http://89.116.250.104:80",
    "http://45.67.215.76:80",
    "http://45.67.215.60:80",
    "http://102.177.176.189:80",
    "http://119.40.98.26:20",
    "http://216.205.52.107:80",
    "http://141.101.115.253:80",
    "http://185.238.228.124:80",
    "http://84.22.48.28:8080",
    "http://216.205.52.233:80",
    "http://45.67.215.147:80",
    "http://102.177.176.251:80",
    "http://69.84.182.52:80",
    "http://185.238.228.149:80",
    "http://102.177.176.93:80",
    "http://69.84.182.40:80",
    "http://69.84.182.4:80",
    "http://185.221.160.238:80",
    "http://102.177.176.201:80",
    "http://170.114.45.52:80",
    "http://216.205.52.10:80",
    "http://170.114.45.244:80",
    "http://69.84.182.1:80",
    "http://170.114.46.159:80",
    "http://170.114.46.121:80",
    "http://69.84.182.220:80",
    "http://138.0.207.3:8085",
    "http://216.205.52.47:80",
    "http://45.67.215.20:80",
    "http://103.160.204.198:80",
    "http://170.114.45.182:80",
    "http://141.101.115.10:80",
    "http://69.84.182.63:80",
    "http://141.101.120.168:80",
    "http://185.221.160.33:80",
    "http://102.177.176.120:80",
    "http://45.67.215.55:80",
    "http://45.67.215.15:80",
    "http://89.116.250.170:80",
    "http://89.116.250.216:80",
    "http://102.177.176.83:80",
    "http://170.114.46.162:80",
    "socks4://115.243.142.185:5678",
    "http://216.205.52.110:80",
    "http://45.8.211.129:80",
    "http://216.205.52.39:80",
    "http://69.84.182.210:80",
    "socks4://115.85.86.114:5678",
    "http://141.101.120.205:80",
    "http://102.177.176.41:80",
    "http://170.114.46.130:80",
    "http://102.177.176.238:80",
    "http://216.205.52.88:80",
    "http://8.212.165.164:5003",
    "socks4://123.108.98.89:5678",
    "http://216.205.52.99:80",
    "http://45.67.215.200:80",
    "http://216.205.52.31:80",
    "http://141.101.120.112:80",
    "http://103.116.7.114:80",
    "http://216.205.52.247:80",
    "http://216.205.52.191:80",
    "http://45.67.215.100:80",
    "http://141.101.113.23:80",
    "http://89.116.250.61:80",
    "http://185.221.160.141:80",
    "http://170.114.45.176:80",
    "http://170.114.45.187:80",
    "http://216.205.52.96:80",
    "http://170.114.45.181:80",
    "http://102.177.176.28:80",
    "http://45.8.211.144:80",
    "http://216.205.52.79:80",
    "http://117.161.170.163:9482",
    "http://102.177.176.148:80",
    "http://102.177.176.64:80",
    "http://185.221.160.44:80",
    "http://45.8.211.120:80",
    "http://170.114.45.83:80",
    "http://72.10.160.93:28583",
    "http://89.116.250.189:80",
    "http://216.205.52.248:80",
    "http://170.114.45.242:80",
    "http://69.84.182.238:80",
    "http://45.67.215.108:80",
    "http://216.24.57.139:80",
    "http://170.114.45.51:80",
    "http://185.221.160.237:80",
    "http://45.67.215.144:80",
    "http://141.101.120.108:80",
    "http://69.84.182.173:80",
    "http://185.238.228.105:80",
    "http://170.114.45.160:80",
    "http://69.84.182.29:80",
    "http://89.116.250.179:80",
    "http://170.114.45.226:80",
    "http://185.221.160.56:80",
    "http://216.205.52.122:80",
    "http://141.101.120.157:80",
    "http://141.101.120.164:80",
    "http://185.221.160.242:80",
    "http://170.114.46.223:80",
    "http://185.221.160.16:80",
    "socks5://117.74.65.207:443",
    "http://141.101.120.212:80",
    "http://185.221.160.52:80",
    "http://89.116.250.89:80",
    "http://113.204.79.230:9091",
    "http://69.84.182.236:80",
    "http://69.84.182.218:80",
    "http://141.101.114.50:80",
    "http://141.101.120.182:80",
    "http://108.162.195.129:80",
    "http://45.67.215.45:80",
    "http://89.116.250.219:80",
    "http://216.205.52.152:80",
    "http://69.84.182.185:80",
    "http://216.205.52.62:80",
    "http://141.101.120.127:80",
    "http://170.114.46.0:80",
    "http://45.67.215.202:80",
    "http://216.205.52.102:80",
    "http://141.101.113.102:80",
    "http://102.177.176.65:80",
    "http://141.101.120.139:80",
    "http://170.114.46.191:80",
    "http://216.205.52.37:80",
    "http://103.116.7.150:80",
    "http://45.67.215.57:80",
    "http://89.116.250.180:80",
    "http://185.221.160.146:80",
    "http://216.205.52.171:80",
    "http://216.205.52.146:80",
    "http://170.114.45.16:80",
    "http://141.101.120.0:80",
    "http://185.238.228.104:80",
    "http://89.116.250.156:80",
    "http://108.162.198.166:80",
    "http://108.162.198.64:80",
    "http://69.84.182.88:80",
    "http://69.84.182.171:80",
    "http://45.67.215.11:80",
    "http://141.101.120.195:80",
    "http://170.114.45.218:80",
    "http://108.162.198.161:80",
    "http://69.84.182.208:80",
    "http://170.114.46.139:80",
    "http://103.160.204.122:80",
    "http://170.114.46.198:80",
    "http://141.101.120.204:80",
    "http://141.101.115.248:80",
    "http://185.221.160.84:80",
    "http://103.149.238.100:1111",
    "http://170.114.45.203:80",
    "http://141.101.120.140:80",
    "http://185.221.160.177:80",
    "http://103.160.204.129:80",
    "http://45.67.215.36:80",
    "http://69.84.182.23:80",
    "http://89.116.250.249:80",
    "http://185.221.160.195:80",
    "http://103.160.204.55:80",
    "http://170.114.45.6:80",
    "http://45.67.215.26:80",
    "http://108.162.196.72:80",
    "http://45.67.215.198:80",
    "http://108.162.194.129:80",
    "http://108.162.193.190:80",
    "http://141.101.113.68:80",
    "http://216.205.52.160:80",
    "http://45.8.211.183:80",
    "socks4://17.144.243.221:1337",
    "http://141.101.120.223:80",
    "http://69.84.182.48:80",
    "socks4://67.43.228.253:19173",
    "http://45.8.211.13:80",
    "http://110.76.144.254:8080",
    "http://45.67.215.178:80",
    "http://69.84.182.211:80",
    "http://185.221.160.201:80",
    "http://113.192.30.217:8081",
    "socks4://114.102.45.42:8089",
    "http://216.205.52.213:80",
    "http://120.89.91.222:8181",
    "http://170.114.46.205:80",
    "http://216.205.52.46:80",
    "http://216.205.52.185:80",
    "http://170.114.46.175:80",
    "http://45.8.211.134:80",
    "http://216.205.52.249:80",
    "http://89.116.250.13:80",
    "http://141.101.113.24:80",
    "http://216.205.52.90:80",
    "http://102.177.176.123:80",
    "http://89.116.250.127:80",
    "http://170.114.46.178:80",
    "http://102.177.176.214:80",
    "http://170.114.45.247:80",
    "http://170.114.45.251:80",
    "http://185.221.160.101:80",
    "http://185.238.228.132:80",
    "http://102.177.176.40:80",
    "http://141.101.120.10:80",
    "http://85.159.230.88:3128",
    "http://185.221.160.124:80",
    "http://108.162.192.156:80",
    "http://108.162.198.208:80",
    "http://89.116.250.171:80",
    "http://141.101.120.113:80",
    "http://89.116.250.176:80",
    "http://69.84.182.57:80",
    "http://170.114.45.189:80",
    "http://45.8.211.226:80",
    "http://45.67.215.37:80",
    "http://170.114.45.200:80",
    "http://114.231.72.225:1080",
    "http://216.205.52.138:80",
    "http://141.101.120.236:80",
    "http://185.221.160.243:80",
    "http://45.67.215.82:80",
    "http://170.114.45.23:80",
    "http://170.114.46.203:80",
    "http://185.238.228.109:80",
    "http://108.162.193.74:80",
    "http://69.84.182.6:80",
    "http://69.84.182.103:80",
    "http://185.221.160.236:80",
    "http://103.116.7.1:80",
    "http://108.162.193.100:80",
    "http://102.177.176.92:80",
    "http://170.114.45.161:80",
    "http://216.24.57.138:80",
    "http://108.162.192.55:80",
    "http://216.205.52.159:80",
    "http://139.135.145.198:5050",
    "http://185.221.160.194:80",
    "http://216.205.52.163:80",
    "http://141.101.120.131:80",
    "http://185.238.228.134:80",
    "http://170.114.46.116:80",
    "http://108.162.193.107:80",
    "http://216.205.52.190:80",
    "http://89.116.250.140:80",
    "http://185.238.228.142:80",
    "http://108.162.193.209:80",
    "http://69.84.182.3:80",
    "http://216.205.52.144:80",
    "http://216.205.52.130:80",
    "http://141.101.120.115:80",
    "http://45.67.215.41:80",
    "http://185.238.228.123:80",
    "http://216.205.52.182:80",
    "http://170.114.46.141:80",
    "http://141.101.120.37:80",
    "http://103.160.204.112:80",
    "http://45.8.211.178:80",
    "http://185.238.228.152:80",
    "http://108.162.198.72:80",
    "http://170.114.46.182:80",
    "http://141.101.120.245:80",
    "http://102.177.176.237:80",
    "http://89.116.250.114:80",
    "http://141.101.120.240:80",
    "http://185.221.160.102:80",
    "http://141.101.120.177:80",
    "http://141.101.120.201:80",
    "http://89.116.250.29:80",
    "http://89.116.250.0:80",
    "http://108.162.195.101:80",
    "http://45.67.215.161:80",
    "http://141.101.120.181:80",
    "http://138.68.60.8:80",
    "http://102.177.176.74:80",
    "http://185.221.160.189:80",
    "http://108.162.198.206:80",
    "http://170.114.46.122:80",
    "http://69.84.182.189:80",
    "http://45.67.215.255:80",
    "http://185.221.160.66:80",
    "http://45.8.211.124:80",
    "http://141.101.115.243:80",
    "http://108.162.192.90:80",
    "http://185.238.228.102:80",
    "http://170.114.45.15:80",
    "socks4://0.0.0.36:3128",
    "http://216.24.57.212:80",
    "http://170.114.45.79:80",
    "http://108.141.130.146:80",
    "http://89.116.250.92:80",
    "http://91.193.58.139:80",
    "http://69.84.182.252:80",
    "http://141.101.120.192:80",
    "http://45.67.215.77:80",
    "http://185.221.160.192:80",
    "http://216.205.52.44:80",
    "http://170.114.45.216:80",
    "http://103.154.178.106:8080",
    "http://45.67.215.21:80",
    "http://103.160.204.0:80",
    "http://113.108.105.30:9091",
    "http://170.114.46.123:80",
    "http://216.205.52.137:80",
    "http://69.84.182.152:80",
    "http://72.10.160.91:1585",
    "http://170.114.46.111:80",
    "http://170.114.45.41:80",
    "http://141.101.115.252:80",
    "http://170.114.45.17:80",
    "http://69.84.182.47:80",
    "http://170.114.45.40:80",
    "http://89.116.250.129:80",
    "http://216.205.52.180:80",
    "http://170.114.46.208:80",
    "http://170.114.45.225:80",
    "http://108.162.196.118:80",
    "http://45.67.215.124:80",
    "http://216.205.52.133:80",
    "http://89.116.250.178:80",
    "http://45.67.215.223:80",
    "http://216.205.52.244:80",
    "http://45.67.215.73:80",
    "http://216.205.52.203:80",
    "http://102.177.176.168:80",
    "http://45.8.211.111:80",
    "http://69.84.182.140:80",
    "http://69.84.182.16:80",
    "http://216.205.52.19:80",
    "http://141.101.120.134:80",
    "http://185.221.160.63:80",
    "http://141.101.115.36:80",
    "http://185.238.228.18:80",
    "http://170.114.45.108:80",
    "http://216.205.52.92:80",
    "http://108.162.198.19:80",
    "http://216.24.57.118:80",
    "http://170.114.45.121:80",
    "http://138.117.230.131:999",
    "http://102.177.176.87:80",
    "http://108.162.193.108:80",
    "http://103.160.204.106:80",
    "http://45.236.44.94:8080",
    "http://141.101.120.187:80",
    "http://141.101.115.101:80",
    "http://89.116.250.58:80",
    "http://170.114.45.252:80",
    "http://102.177.176.106:80",
    "http://170.114.45.185:80",
    "http://185.221.160.143:80",
    "http://89.116.250.135:80",
    "http://185.221.160.167:80",
    "http://170.114.45.43:80",
    "http://126.209.50.252:1234",
    "http://141.101.120.148:80",
    "http://185.221.160.3:80",
    "http://216.205.52.225:80",
    "http://89.116.250.188:80",
    "http://45.70.202.161:999",
    "http://69.84.182.33:80",
    "http://141.101.120.207:80",
    "http://216.205.52.236:80",
    "http://89.116.250.244:80",
    "http://102.177.176.98:80",
    "http://170.114.45.68:80",
    "http://216.205.52.73:80",
    "http://141.101.120.122:80",
    "http://45.67.215.207:80",
    "http://112.211.64.112:8082",
    "http://45.67.215.75:80",
    "http://119.18.146.92:9090",
    "http://216.205.52.64:80",
    "http://216.205.52.112:80",
    "http://69.84.182.229:80",
    "http://185.238.228.144:80",
    "http://115.76.203.198:8080",
    "http://89.116.250.148:80",
    "http://89.116.250.147:80",
    "http://170.114.46.126:80",
    "http://89.116.250.195:80",
    "http://185.238.228.10:80",
    "http://141.101.115.251:80",
    "http://170.114.45.205:80",
    "http://89.116.250.38:80",
    "http://185.221.160.26:80",
    "http://216.205.52.245:80",
    "http://185.238.228.0:80",
    "http://69.84.182.18:80",
    "http://141.101.113.2:80",
    "http://216.205.52.125:80",
    "http://103.160.204.10:80",
    "http://216.205.52.28:80",
    "http://89.116.250.137:80",
    "http://170.114.45.78:80",
    "http://45.67.215.68:80",
    "http://45.8.211.115:80",
    "http://89.116.250.16:80",
    "http://102.177.176.241:80",
    "http://216.205.52.21:80",
    "http://69.84.182.34:80",
    "http://89.116.250.120:80",
    "http://108.162.193.189:80",
    "http://170.114.45.148:80",
    "http://1.1.189.58:8080",
    "http://103.153.246.142:8181",
    "http://170.114.45.217:80",
    "http://103.10.171.114:8080",
    "http://69.84.182.96:80",
    "http://69.84.182.41:80",
    "http://170.114.45.210:80",
    "http://45.67.215.136:80",
    "http://69.84.182.243:80",
    "http://69.84.182.137:80",
    "http://185.221.160.74:80",
    "http://69.84.182.237:80",
    "http://112.198.132.107:8082",
    "http://185.238.228.133:80",
    "http://114.237.77.229:1080",
    "http://89.116.250.224:80",
    "http://216.205.52.114:80",
    "http://45.8.211.128:80",
    "http://45.67.215.180:80",
    "http://141.101.120.20:80",
    "http://89.116.250.3:80",
    "http://170.114.45.197:80",
    "http://216.205.52.168:80",
    "http://102.177.176.45:80",
    "http://185.221.160.204:80",
    "http://114.198.244.57:3128",
    "http://216.24.57.110:80",
    "http://45.67.215.7:80",
    "http://216.205.52.7:80",
    "http://8.39.125.243:80",
    "http://185.221.160.80:80",
    "http://216.205.52.27:80",
    "http://141.101.120.183:80",
    "http://108.162.192.123:80",
    "http://102.177.176.191:80",
    "http://108.162.192.87:80",
    "http://185.221.160.137:80",
    "http://69.84.182.7:80",
    "http://141.101.120.215:80",
    "http://45.67.215.171:80",
    "http://170.114.45.170:80",
    "http://185.238.228.120:80",
    "http://45.8.211.132:80",
    "http://45.8.211.123:80",
    "http://141.101.115.250:80",
    "http://45.67.215.5:80",
    "http://102.177.176.61:80",
    "http://216.205.52.104:80",
    "http://69.84.182.245:80",
    "http://89.116.250.242:80",
    "http://216.205.52.165:80",
    "http://141.101.120.141:80",
    "http://170.114.46.119:80",
    "http://185.221.160.7:80",
    "http://103.127.220.62:8080",
    "http://170.114.45.74:80",
    "http://216.205.52.142:80"
]

# === Calculate Upcoming Friday–Sunday Dates ===
def get_upcoming_weekend_dates():
    today = datetime.today()
    days_until_friday = (4 - today.weekday()) % 7
    friday = today + timedelta(days=days_until_friday + 0)
    return [today + timedelta(days=1), today + timedelta(days=3)]
    #return [friday, friday + timedelta(days=1), friday + timedelta(days=2)]

# === HTML Output ===
def generate_html(events):
    dates = get_upcoming_weekend_dates()
    title = f"🎉 Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}"
    
    html_output = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>{title}</title>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/buttons/2.4.1/css/buttons.dataTables.min.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/responsive/2.5.0/css/responsive.dataTables.min.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/searchbuilder/1.5.0/css/searchBuilder.dataTables.min.css">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; border: 1px solid #ccc; vertical-align: top; }}
            img {{ max-width: 150px; height: auto; border-radius: 10px; }}
            .dtsb-title {{ display: none; }}
            button {{ background-color: black !important; color: white !important; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <table id="events">
            <thead>
                <tr>
		    <th>Image</th>
                    <th>Title</th>
                    <th>Date</th>
                    <th>Price</th>
                    <th>Description</th>
                    <th>Source</th>
                </tr>
            </thead>
            <tbody>
    """

    for e in events:
        if not e.get('title') or not e.get('url'):
            continue
        html_output += f"""
            <tr>
                <td>{f'<img src="{html.escape(e["image"])}">' if e.get('image', '').startswith('http') else ''}</td>
                <td><a href="{html.escape(e['url'])}" target="_blank">{html.escape(e['title'])}</a></td>
                <td>{html.escape(e.get('date', ''))}</td>
                <td>{html.escape(e.get('price', ''))}</td>
                <td>{html.escape(e.get('description', ''))}</td>
                <td>{html.escape(e.get('source', ''))}</td>
            </tr>
        """

    html_output += """
            </tbody>
        </table>

        <!-- jQuery + DataTables JS -->
        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/dataTables.buttons.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.html5.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.print.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.colVis.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.68/pdfmake.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.68/vfs_fonts.js"></script>
        <script src="https://cdn.datatables.net/responsive/2.5.0/js/dataTables.responsive.min.js"></script>
        <script src="https://cdn.datatables.net/searchbuilder/1.5.0/js/dataTables.searchBuilder.min.js"></script>

        <script>
        function addFancyRandomEventButtonBelowH1() {
                const dt = $('#events').DataTable();
                if (!dt) return console.warn("⚠️ DataTable not ready.");

                // Track already shown events
                let shownIndices = [];

                // Remove any existing random button
                try { dt.buttons('.random-event').remove(); } catch (e) {}

                dt.button().add(null, {
                        text: '🎲 Random Event Picker',
                        className: 'random-event btn btn-outline-primary',
                        action: function () {
                                const rowsArr = dt.rows({ search: 'applied' }).nodes().toArray();
                                if (!rowsArr.length) return alert("No visible events to pick from.");

                                // Reset if all events have been shown
                                if (shownIndices.length >= rowsArr.length) {
                                        shownIndices = [];
                                        console.log("♻️ All events shown — starting over.");
                                }

                                // Get a random unused index
                                let randIndex;
                                do {
                                        randIndex = Math.floor(Math.random() * rowsArr.length);
                                } while (shownIndices.includes(randIndex));

                                shownIndices.push(randIndex);
                                const row = rowsArr[randIndex];

                                // ✅ Title/link is column 2; Image is column 1
                                const linkEl = row.querySelector("td:nth-child(2) a");
                                const imgEl  = row.querySelector("td:nth-child(1) img");

                                const title = linkEl?.textContent.trim() || "No title";
                                const href  = linkEl?.href || "#";
                                const image = imgEl?.src || "";

                                document.getElementById('random-event-card')?.remove();

                                const card = document.createElement("div");
                                card.id = "random-event-card";
                                card.style = `
                                        border: 1px solid #ccc; border-left: 5px solid #007acc;
                                        padding: 16px; margin-top: 20px; max-width: 600px;
                                        border-radius: 8px; position: relative; background: #f9f9f9;
                                        font-family: sans-serif;
                                `;
                                card.innerHTML = `
                                        <button style="
                                                position: absolute; top: 8px; right: 10px; background: transparent;
                                                border: none; font-size: 20px; cursor: pointer; color: #999;"
                                                onclick="document.getElementById('random-event-card').remove()">×</button>
                                        <h3 style="margin: 0 0 10px">🎯 Your Random Pick:</h3>
                                        <a href="${href}" target="_blank" style="font-size: 16px; font-weight: bold; color: #007acc;">${title}</a>
                                        ${image ? `<div><img src="${image}" style="margin-top: 10px; max-width: 100%; border-radius: 6px;" /></div>` : ''}
                                `;

                                const h1 = document.querySelector("h1");
                                if (h1) h1.insertAdjacentElement("afterend", card);
                        }
                });
        }

        (function waitForTableAndUpgrade(retries = 10) {
          const tableEl = document.querySelector("#events");
          if (!tableEl || !tableEl.querySelector("thead")) {
            if (retries > 0) return setTimeout(() => waitForTableAndUpgrade(retries - 1), 500);
            else return console.warn("❌ Table not found.");
          }

          if ($.fn.DataTable.isDataTable("#events")) $('#events').DataTable().destroy();

          if (!tableEl.querySelector("tfoot")) {
            const tfoot = tableEl.querySelector("thead").cloneNode(true);
            tfoot.querySelectorAll("th").forEach(cell => cell.innerHTML = "");
            tableEl.appendChild(tfoot);
          }

          $('#events').DataTable({
            responsive: true,
            paging: false,
            ordering: true,
            info: false,
            dom: 'QBfrtip',
            buttons: ['csv', 'excel'],
            searchBuilder: { columns: true },
            columnDefs: [{ targets: -1, orderable: false }],
            initComplete: function () {
              this.api().columns().every(function () {
                const input = document.createElement("input");
                input.placeholder = "Filter...";
                input.style.width = "100%";
                $(input).appendTo($(this.footer()).empty())
                  .on("keyup change clear", function () {
                    this.search(this.value).draw();
                  }.bind(this));
              });
              addFancyRandomEventButtonBelowH1();
            }
          });
        })();
        </script>
    </body>
    </html>
    """
    return html_output

# === Scrapers ===
async def scrape_eventbrite(page):
    print("🔍 Scraping Eventbrite...")
    events = []
    target_dates = [(d.strftime('%b %d')) for d in get_upcoming_weekend_dates()]
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%d")
    end_str = dates[-1].strftime("%Y-%m-%d")
    url = f"https://www.eventbrite.ca/d/canada--toronto/events/?start_date={start_str}&end_date={end_str}"
    await page.goto(url)
    content = await page.content()
    print(content)

    while True:
        print("🔄 Scrolling to load events on current page...")
        prev_height = 0
        retries = 0
        while retries < 5:
            await page.mouse.wheel(0, 5000)
            await asyncio.sleep(1.2)
            curr_height = await page.evaluate("document.body.scrollHeight")
            if curr_height == prev_height:
                retries += 1
            else:
                retries = 0
                prev_height = curr_height

        cards = await page.query_selector_all("li [data-testid='search-event']")
        print(f"🧾 Found {len(cards)} event cards on this page.")

        for card in cards:
            try:
                title_el = await card.query_selector("h3")
                title = (await title_el.inner_text()).strip() if title_el else "N/A"

                date_el = await card.query_selector("a + p.Typography_root__487rx")
                location_el = await card.query_selector(".Typography_root__487rx.Typography_body-md__487rx")
                date_text = (await date_el.inner_text()).strip() if date_el else "N/A"
                location_text = (await location_el.inner_text()).strip() if location_el else "N/A"
                date_text = date_text

                img_el = await card.query_selector("img.event-card-image")
                img_url = await img_el.get_attribute("src") if img_el else ""

                link_el = await card.query_selector("a.event-card-link")
                link = await link_el.get_attribute("href") if link_el else ""

                price_el = await card.query_selector("div[class*='priceWrapper'] p")
                price = (await price_el.inner_text()).strip() if price_el else "Free"

                events.append({
                    "title": title,
                    "date": date_text,
                    "description": location_text,
                    "image": img_url,
                    "url": link,
                    "price": price,
                    "source": "Eventbrite"
                })
            except Exception as e:
                print("⚠️ Error extracting event:", e)

        try:
            next_btn = await page.query_selector('[data-testid="page-next"]:not([aria-disabled="true"])')
            if next_btn:
                print("➡️ Going to next page...")
                await next_btn.click()
                await asyncio.sleep(2)
            else:
                print("🛑 No more pages.")
                break
        except Exception as e:
            print("⚠️ Pagination error:", e)
            break
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

async def scrape_fever(page):
    print("🔍 Scraping Fever...") 
    events = []
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%d")
    end_str = dates[-1].strftime("%Y-%m-%d")
    url = f"https://feverup.com/en/toronto/things-to-do?date={start_str}until{end_str}"
    await page.goto(url)
    await page.wait_for_selector('li[data-testid="fv-wpf-plan-grid__list-item"]')

    previous_height = 0
    retries = 0
    while retries < 5:
        current_height = await page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            retries += 1
            await asyncio.sleep(1)
        else:
            await page.mouse.wheel(0, current_height)
            previous_height = current_height
            retries = 0
            await asyncio.sleep(1.5)

    cards = await page.query_selector_all('li[data-testid="fv-wpf-plan-grid__list-item"]')
    for card in cards:
        try:
            title = await card.eval_on_selector('[data-testid="fv-plan-card-title"]', 'el => el.textContent')
            date = await card.eval_on_selector('[data-testid="fv-plan-card-v2__date-range"]', 'el => el.textContent')
            price = await card.eval_on_selector('[data-testid="fv-plan-card-v2__price"]', 'el => el.textContent')
            link_el = await card.query_selector('a.fv-plan-card-v2')
            url = await link_el.get_attribute('href') if link_el else ''
            img = await card.eval_on_selector("img", "el => el.getAttribute('src')") or ""
            if not url.startswith("http"): url = "https://feverup.com" + url
            events.append({
                "title": title.strip(), "date": date.strip(), "description": "",
                "image": img.strip(), "url": url.strip(), "price": price.strip(), "source": "Fever"
            })
        except:
            continue
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

async def scrape_meetup(page):
    print("🔍 Scraping Meetup...")
    events = []
    url = "https://www.meetup.com/find/?location=ca--on--Toronto&source=EVENTS&customStartDate=2025-07-25T00%3A00%3A00-04%3A00&customEndDate=2025-07-27T23%3A59%3A00-04%3A00&eventType=inPerson"
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%dT00%%3A00%%3A00-04%%3A00")  # URL encoded "T00:00:00-04:00"
    end_str = dates[-1].strftime("%Y-%m-%dT23%%3A59%%3A00-04%%3A00")
    url = f"https://www.meetup.com/find/?location=ca--on--Toronto&source=EVENTS&customStartDate={start_str}&customEndDate={end_str}&eventType=inPerson"
    await page.goto(url)

    retries = 0
    prev_height = 0
    while retries < 5:
        await page.mouse.wheel(0, 5000)
        await asyncio.sleep(2)
        curr_height = await page.evaluate("document.body.scrollHeight")
        if curr_height == prev_height:
            retries += 1
        else:
            prev_height = curr_height
            retries = 0

    raw_events = await page.evaluate("""
        () => Array.from(document.querySelectorAll("a[href*='/events/']")).map(e => ({
            title: e.querySelector("h3")?.innerText || "N/A",
            date: e.querySelector("time")?.innerText || "N/A",
            url: e.href,
            image: e.querySelector("img")?.src || "",
            desc: e.querySelector("p")?.innerText || ""
        }))
    """)
    for e in raw_events:
        events.append({
            "title": e['title'], "date": e['date'], "description": e['desc'],
            "image": e['image'], "url": e['url'], "price": "Free", "source": "Meetup"
        })
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

async def scrape_stubhub(page):
    print("🔍 Scraping StubHub...")

    # Step 1: Go to Explore
    await page.goto("https://www.stubhub.ca/explore?lat=NDMuNzA0MjkxMDgyNzI4Mjk%3D&lon=LTc5LjQyNDgxODg3Mjg4NTkx", timeout=60000)
    await page.wait_for_timeout(3000)

    # Step 2: Set location to Toronto
    try:
        await page.click("div[role='combobox']", timeout=5000)
        await page.wait_for_selector("input[placeholder='Search location']", timeout=10000)
        await page.fill("input[placeholder='Search location']", "Toronto")
        await page.wait_for_timeout(2000)
        toronto_option = await page.query_selector("ul[role='listbox'] li:has-text('Toronto, ON, Canada')")
        if toronto_option:
            await toronto_option.click()
        else:
            print("❌ 'Toronto, ON, Canada' option not found.")
            return []
        await page.wait_for_timeout(5000)
    except Exception as e:
        print(f"❌ Failed to select Toronto location: {e}")
        #return []

    # Step 3: Open Date dropdown
    try:
        await page.click("div[aria-label='Filter by date']")
        await page.click("[role='dialog'] > div > div:last-child", timeout=3000)
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"❌ Failed to open or click Custom Dates: {e}")
        return []

    # Step 4: Click the correct date range in calendar
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime('%a %b %d %Y')  # e.g. 'Fri Aug 01 2025'
    end_str = dates[-1].strftime('%a %b %d %Y')    # e.g. 'Sun Aug 03 2025'

    # click "next month" if August is not shown
    for i in range(3):
        if not await page.query_selector(f"[aria-label='{start_str}']"):
            next_btn = await page.query_selector("button[aria-label='Next Month']")
            if next_btn:
                await next_btn.click()
                await page.wait_for_timeout(1000)
        else:
            break

    try:
        await page.click(f"[aria-label='{start_str}']")
        await page.wait_for_timeout(300)
        await page.click(f"[aria-label='{end_str}']")
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"❌ Failed selecting dates {start_str} to {end_str}: {e}")
        return []

    # Step 5: Load all listings via scroll + "Show More"
    max_scrolls = 15
    for _ in range(max_scrolls):
        await page.mouse.wheel(0, 8000)
        await page.wait_for_timeout(1500)

        show_more = await page.query_selector("button.sc-ikkxIA.dplCTc")
        if show_more:
            try:
                await show_more.click()
                await page.wait_for_timeout(3000)
            except:
                break
        else:
            break

    # Step 5: Wait for event cards
    try:
        await page.wait_for_selector("li > div", timeout=10000)
    except:
        print("❌ Event listings not found.")
        return []

    # Step 6: Scrape events
    events = []
    cards = await page.query_selector_all("li > div")
    for card in cards:
        try:
            title_el = await card.query_selector("a p:nth-child(1)")
            datetime_el = await card.query_selector_all("a p:nth-child(2)")
            venue_el = await card.query_selector_all("a p:nth-child(3)")
            link_el = await card.query_selector("a")
            img_el = await card.query_selector("img")

            title = await title_el.inner_text() if title_el else "N/A"
            datetime_text = (await datetime_el[0].inner_text()).strip() if datetime_el else "N/A"
            venue = (await venue_el[0].inner_text()).strip() if venue_el else "N/A"
            link = await link_el.get_attribute("href") if link_el else ""
            image = await img_el.get_attribute("src") if img_el else "N/A"


            events.append({
                "source": "StubHub",
                "title": title.strip(),
                "date": datetime_text.strip(),
                "description": venue.strip(),
                "url": link if link.startswith("http") else f"https://www.stubhub.ca{link}",
                "price": "N/A",
                "image": image
            })
        except Exception as e:
            print(f"⚠️ Error parsing card: {e}")
            continue

    print(f"✅ StubHub: Scraped {len(events)} events.")

    return events



async def scrape_blogto(page):
    print("🔍 Scraping BlogTO...")
    await page.goto("https://www.blogto.com/events/")
    await page.wait_for_selector(".event-info-box")

    target_days = get_upcoming_weekend_dates()
    events, seen = [], set()

    for day in target_days:
        try:
            selector = f'button[data-pika-year="{day.year}"][data-pika-month="{day.month - 1}"][data-pika-day="{day.day}"]'
            await page.click(selector)
            await asyncio.sleep(2)  # allow events to load
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            for card in soup.select(".event-info-box"):
                title_el = card.select_one(".event-info-box-title-link")
                if not title_el:
                    continue
                title = title_el.text.strip()
                if title in seen:
                    continue
                seen.add(title)

                date_text = card.select_one(".event-info-box-date").text.strip() if card.select_one(".event-info-box-date") else "N/A"
                desc = card.select_one(".event-info-box-description").text.strip() if card.select_one(".event-info-box-description") else ""
                image = card.select_one(".event-info-box-image")["src"] if card.select_one(".event-info-box-image") else ""
                url = title_el['href']

                events.append({
                    "title": title,
                    "date": f"{day.strftime('%A %B %d')} {date_text}" if date_text != "N/A" else day.strftime('%A %B %d'),
                    "description": desc,
                    "image": image,
                    "url": url,
                    "price": "N/A",
                    "source": "BlogTO"
                })

        except Exception as e:
            print(f"⚠️ Error on {day.strftime('%Y-%m-%d')}: {e}")
            continue
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

def send_email_with_attachment(to_email, subject, html_path):
    from_email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_PASS")  # Use an App Password, not your Gmail password

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach body
    msg.attach(MIMEText("open your 'Toronto Weekend Events' HTML file and book an event 2 weeks from now for your social life.", 'plain'))

    # Attach the file
    with open(html_path, "rb") as file:
        part = MIMEApplication(file.read(), Name="weekend_events_toronto.html")
        part['Content-Disposition'] = 'attachment; filename="weekend_events_toronto.html"'
        msg.attach(part)

    # Send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(from_email, app_password)
        server.send_message(msg)
    print("📧 Email sent!")


def get_random_proxy():
   """Return a random proxy from the list in Playwright format."""
   proxy = random.choice(PROXY_LIST)
   # Playwright expects {'server': url}, can also handle socks4/socks5
   return {"server": proxy}

# === Main Runner ===
async def aggregate_events():
    dates = get_upcoming_weekend_dates()
    print(f"📆 Scraping for: {[d.strftime('%Y-%m-%d') for d in dates]}")
    all_events = []
	
	# Add retry logic for proxy failures
    max_attempts = 5
    attempt = 0
    success = False

    while attempt < max_attempts and not success:
        proxy = get_random_proxy()
        print(f"🛡️ Using proxy: {proxy['server']} (Attempt {attempt+1}/{max_attempts})")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,
                    proxy=proxy,
                    slow_mo=50
                )
                page = await browser.new_page()
                all_events += await scrape_eventbrite(page)
                # You can add other scrapers here as needed
                await browser.close()
                success = True  # If no exception, mark success
        except Exception as e:
            print(f"⚠️ Proxy failed: {proxy['server']} — {e}")
            attempt += 1
            await asyncio.sleep(2)  # Wait before next attempt

        # 🧹 De-duplicate by title only
        seen_titles = set()
        deduped_events = []
        for event in all_events:
            title_key = event['title'].strip().lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                deduped_events.append(event)
        all_events = deduped_events


    html_output = generate_html(all_events)
    with open("weekend_events_toronto.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    print("✅ File saved: weekend_events_toronto.html")


    # Send the email
    #send_email_with_attachment(
    #    to_email=os.getenv("EMAIL_TO"),
    #    subject = f"🎉 Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}",
    #    html_path="weekend_events_toronto.html"
    #)

if __name__ == "__main__":
    asyncio.run(aggregate_events())






















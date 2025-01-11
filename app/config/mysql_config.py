# coding: utf-8
import platform

if platform.system() in ['Windows', 'Darwin']:
    HOST = 'localhost:3306'
    USER = 'root'
    PASSWORD = '123'
    DATABASE = 'ry-vue-test'
else:
    HOST = 'localhost:3306'
    USER = 'root'
    PASSWORD = '123'
    DATABASE = 'ry-vue'

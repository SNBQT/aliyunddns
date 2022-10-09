#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import re
import sys
from datetime import datetime

import yaml
from aliyunsdkalidns.request.v20150109 import (DescribeDomainRecordInfoRequest,
                                               DescribeDomainRecordsRequest,
                                               UpdateDomainRecordRequest)
from aliyunsdkcore import client

with open(sys.path[0]+'/setting.yaml', 'r', encoding='utf-8') as f:
    s = yaml.safe_load(f)
    # print(yaml.dump(s,default_flow_style=False)) # 输出yaml文件内容

# 阿里云 Access Key ID
access_key_id = s['access_key_id']
# 阿里云 Access Key Secret
access_key_secret = s['access_key_secret']
# 阿里云 一级域名
rc_domain = s['rc_domain']
# 解析记录
rc_rr_list = s['rc_rr_list']
# 返回内容格式
rc_format = 'json'


def check_records(dns_domain):
    """获取域名的解析信息

    Args:
        dns_domain (_type_): _description_

    Returns:
        _type_: _description_
    """
    clt = client.AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
    request = DescribeDomainRecordsRequest.DescribeDomainRecordsRequest()
    request.set_DomainName(dns_domain)
    request.set_accept_format(rc_format)
    result = clt.do_action(request).decode('utf-8')
    result = json.JSONDecoder().decode(result)
    return result


def get_old_ip(record_id):
    """根据域名解析记录ID查询上一次的IP记录

    Args:
        record_id (_type_): _description_

    Returns:
        _type_: _description_
    """
    clt = client.AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
    request = DescribeDomainRecordInfoRequest.DescribeDomainRecordInfoRequest()
    request.set_RecordId(record_id)
    request.set_accept_format(rc_format)
    result = clt.do_action(request)
    result = json.JSONDecoder().decode(result.decode('utf-8'))
    result = result['Value']
    return result


def update_dns(dns_rr, dns_type, dns_value, dns_record_id, dns_ttl, dns_format):
    """更新阿里云域名解析记录信息

    Args:
        dns_rr (_type_): _description_
        dns_type (_type_): _description_
        dns_value (_type_): _description_
        dns_record_id (_type_): _description_
        dns_ttl (_type_): _description_
        dns_format (_type_): _description_

    Returns:
        _type_: _description_
    """
    clt = client.AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
    request = UpdateDomainRecordRequest.UpdateDomainRecordRequest()
    request.set_RR(dns_rr)
    request.set_Type(dns_type)
    request.set_Value(dns_value)
    request.set_RecordId(dns_record_id)
    request.set_TTL(dns_ttl)
    request.set_accept_format(dns_format)
    result = clt.do_action(request)
    return result


def get_my_public_ip():
    """通过 多个网址 获取当前主机的外网IP

    Returns:
        _type_: _description_
    """
    url_list = [
        'http://myip.ipip.net',
        'https://ifconfig.me',
        'http://www.cip.cc',
        'http://ip.3322.net'
    ]
    for url in url_list:
        try:
            cmd = 'curl -s --connect-timeout 5 {}'.format(url)
            print('{} 请求成功'.format(url))
            get_ip_method = os.popen(cmd)
            get_ip_responses = get_ip_method.readlines()[0]
            get_ip_pattern = re.compile(r'\d+\.\d+\.\d+\.\d+')
            get_ip_value = get_ip_pattern.findall(get_ip_responses)
        except:
            print('{} 请求失败'.format(url))
    return get_ip_value


def write_to_file(new_ip):
    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    write_log = open(sys.path[0]+'/aliyun_ddns.txt', 'a')
    write_log.write(('%s %s %s.%s\n') %
                    (time_now, str(new_ip), rc_rr, rc_domain))
    return


if __name__ == '__main__':

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("运行时间: {}".format(now))  # 打印当前时间

    dns_records = check_records(rc_domain)
    # 获取主机当前的IP
    now_ip = get_my_public_ip()[0]

    for rc_rr in rc_rr_list:
        # 之前的解析记录
        old_ip = ""
        record_id = ""
        for record in dns_records["DomainRecords"]["Record"]:
            if record["Type"] == 'A' and record["RR"] == rc_rr:
                record_id = record["RecordId"]
                print("%s.%s recordID: %s" %
                      (record["RR"], rc_domain, record_id))
                if record_id != "":
                    old_ip = get_old_ip(record_id)
                    break

        if record_id == "":
            print(('Warning: Can not find record_id with A record: %s in %s. Please add it first!') % (
                rc_rr, rc_domain))
            continue

        print("%s.%s now host ip: %s\ndns ip: %s" %
              (rc_rr, rc_domain, now_ip, old_ip))

        if old_ip == now_ip:
            print("The specified value of parameter Value is the same as old")
        else:
            rc_type = 'a'               # 记录类型, DDNS填写A记录
            rc_value = now_ip           # 新的解析记录值
            rc_record_id = record_id    # 记录ID
            rc_ttl = '1000'             # 解析记录有效生存时间TTL,单位:秒

            # print(update_dns(rc_rr, rc_type, rc_value,
            #       rc_record_id, rc_ttl, rc_format))
            # write_to_file(now_ip)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Joway 2015年9月4日11:21:16

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
from email.mime.base import MIMEBase
from email.parser import Parser
from email.header import decode_header
import mimetypes
import smtplib
import os

import poplib


def sent_email(from_addr,password,to_addr,subject='',content='',type='plain',filenames=[],from_name='',to_name='',smtp_server=''):
    """
    from_addr = 'xxx@xxx.com'
    password = 'xxxxxxxxxxxxxx'
    to_addr='xxx@xxx.com'
    subject=''
    content=''
    type='xxx',默认为'plain'，支持html
    filenames=['',...]  附件本地全名列表 
    from_name='' 昵称
    to_name=''   昵称
    smtp_server = 'smtp.xxx.com'默认从from_addr中提取smtp地址 
    """
    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))
    def _get_smtp_server(email):
        return ('smtp.' + email[email.find('@') + 1:])
    
    if(smtp_server == ''):
        smtp_server = _get_smtp_server(from_addr)

    msg = MIMEMultipart()
    #msg = MIMEText(content, type, 'utf-8')
    if(from_name != ''):
        msg['From'] = _format_addr('%s <%s>' % from_name,from_addr)
    else:
        msg['From'] = _format_addr('<%s>' % from_addr)
    if(to_name != ''):
        msg['To'] = _format_addr('%s <%s>' % to_name,to_addr)
    else:
        msg['To'] = _format_addr('<%s>' % to_addr)
    if(subject != ''):
        msg['Subject'] = Header(subject, 'utf-8').encode()

    msg.attach(MIMEText(content, type, 'utf-8'))

    # 添加附件就是加上一个MIMEBase，
    if(filenames != []):
        for filename in filenames:
            with open(filename, 'rb') as f:
                # 设置附件的MIME和文件名，这里是png类型:
                str_type=mimetypes.guess_type(filename)[0]
                pass
                mime = MIMEBase(str_type[:str_type.find('/')], str_type[str_type.find('/')+1:], filename=os.path.basename(filename))
                # 加上必要的头信息:
                mime.add_header('Content-Disposition', 'attachment',
                filename=os.path.basename(filename))
                mime.add_header('Content-ID', '<0>')
                mime.add_header('X-Attachment-Id', '0')
                # 把附件的内容读进来:
                mime.set_payload(f.read())
                # 用Base64编码:
                encoders.encode_base64(mime)
                # 添加到MIMEMultipart:
                msg.attach(mime)

    server = smtplib.SMTP(smtp_server, 25)
    server.set_debuglevel(1)
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], msg.as_string())
    server.quit()



def get_email(email,password,pop3_server=''):
    """
    email = 'xxx@xxx.com'
    password = 'xxxxxxxxxxxxxx'
    subject=''
    content=''
    type='xxx',默认为'plain'，支持html
    filenames=['',...]  附件本地全名列表 
    from_name='' 昵称
    to_name=''   昵称
    smtp_server = 'smtp.xxx.com'默认从email中提取smtp地址 
    """
    def _get_pop3_server(email):
        return ('pop.' + email[email.find('@') + 1:])
    def guess_charset(msg):
        charset = msg.get_charset()
        if charset is None:
            content_type = msg.get('Content-Type', '').lower()
            pos = content_type.find('charset=')
            if pos >= 0:
                charset = content_type[pos + 8:].strip()
        return charset

    def decode_str(s):
        value, charset = decode_header(s)[0]
        if charset:
            value = value.decode(charset)
        return value

    def print_info(msg, indent=0):
        if indent == 0:
            for header in ['From', 'To', 'Subject']:
                value = msg.get(header, '')
                if value:
                    if header=='Subject':
                        value = decode_str(value)
                    else:
                        hdr, addr = parseaddr(value)
                        name = decode_str(hdr)
                        value = u'%s <%s>' % (name, addr)
                print('%s%s: %s' % ('  ' * indent, header, value))
        if (msg.is_multipart()):
            parts = msg.get_payload()
            for n, part in enumerate(parts):
                print('%spart %s' % ('  ' * indent, n))
                print('%s--------------------' % ('  ' * indent))
                print_info(part, indent + 1)
        else:
            content_type = msg.get_content_type()
            if content_type=='text/plain' or content_type=='text/html':
                content = msg.get_payload(decode=True)
                charset = guess_charset(msg)
                if charset:
                    content = content.decode(charset)
                print('%sText: %s' % ('  ' * indent, content + '...'))
            else:
                print('%sAttachment: %s' % ('  ' * indent, content_type))

    if(pop3_server == ''):
        pop3_server = _get_pop3_server(email)
    # 连接到POP3服务器:
    server = poplib.POP3(pop3_server)
    # 可以打开或关闭调试信息:
    server.set_debuglevel(1)
    # 可选:打印POP3服务器的欢迎文字:
    print(server.getwelcome().decode('utf-8'))
    # 身份认证:
    server.user(email)
    server.pass_(password)
    # stat()返回邮件数量和占用空间:
    print('Messages: %s. Size: %s' % server.stat())
    # list()返回所有邮件的编号:
    resp, mails, octets = server.list()
    # 可以查看返回的列表类似[b'1 82923', b'2 2184', ...]
    print(mails)
    # 获取最新一封邮件, 注意索引号从1开始:
    index = len(mails)
    resp, lines, octets = server.retr(index)
    # lines存储了邮件的原始文本的每一行,
    # 可以获得整个邮件的原始文本:
    msg_content = b'\r\n'.join(lines).decode('utf-8')
    # 稍后解析出邮件:
    msg = Parser().parsestr(msg_content)
    print_info(msg)
    # 可以根据邮件索引号直接从服务器删除邮件:
    # server.dele(index)
    # 关闭连接:
    server.quit()


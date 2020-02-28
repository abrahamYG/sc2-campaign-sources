#!/usr/bin/env python
import sys
import re
from subprocess import run, PIPE, CompletedProcess
from glob import glob
import logging
import colorlog


def proc_run(x) -> str:
    logging.debug(x)
    p: CompletedProcess = run(x, capture_output=True, shell=True, check=True)
    return p.stdout.decode('utf-8')


def shell_run(cmd, shell=True, check=True) -> str:
    r = run(cmd, shell=shell, universal_newlines=True, stdin=PIPE, stdout=PIPE, check=check)
    return r.stdout.rstrip()


def get_cdn_url(mapster_url):
    content = proc_run(
        f'curl -i -s --http2 --tlsv1.3'
        f' --header "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"'
        f' --compressed'
        f' --header "Accept-Language: en-US,en;q=0.5"'
        f' --header "Upgrade-Insecure-Requests: 1" --user-agent "Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/23.0"'
        f' "{mapster_url}"'
    )
    m = re.search(r'location:\s+(.+)', content, flags=re.I)
    if m:
        logging.debug(m)
        return m.group(1).strip()
    else:
        m = re.search(r'^HTTP/2 404', content)
        if m:
            logging.warning('HTTP-404: %s' % mapster_url)
        else:
            logging.error('failed %s\n%s' % (mapster_url, content))
            sys.exit(1)
        return mapster_url


def main():
    colorlog.logging.basicConfig(level=logging.DEBUG, format='%(log_color)s%(levelname)s%(reset)s (%(funcName)s) %(message)s')
    flist = glob('**/*.json', recursive=True)
    for i, srcf in enumerate(flist):
        logging.info('[%03d/%03d] %s' % (i + 1, len(flist), srcf))
        with open(srcf, mode="r+") as f:
            content = f.read()
            def repl_translate_url(m: re.Match):
                return get_cdn_url(m.group(0))
            content = re.sub(r'https://www\.sc2mapster\.com/projects/[^/]+/files/\d+/download', repl_translate_url, content, flags=re.M)
            f.seek(0)
            f.truncate()
            f.write(content)
    logging.info('DONE')


if __name__ == '__main__':
    main()

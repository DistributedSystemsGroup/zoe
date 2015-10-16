# Copyright (c) 2015, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket
import re
import logging

import dns.ipv4
import dns.ipv6
import dns.name
import dns.query
import dns.tsig
import dns.tsigkeyring
import dns.ttl
import dns.update
import dns.rcode
import dns.reversename
import dns.resolver
from dns.exception import DNSException, SyntaxError

from common.configuration import zoe_conf
from common.exceptions import DDNSUpdateFailed

log = logging.getLogger(__name__)


DEFAULT_TTL = 300


class DDNSUpdater:
    """
    :type keyring: dict
    :type algo: str
    """
    def __init__(self, ttl=DEFAULT_TTL):
        self.server = zoe_conf().ddns_server
        self.keyfile = zoe_conf().ddns_keyfile
        self.keyring = None
        self.algo = None
        self._read_key()
        self.ttl = ttl

    def _get_fqdn(self, hostname):
        return hostname + "." + zoe_conf().ddns_domain

    def _read_key(self):
        try:
            f = open(self.keyfile)
        except FileNotFoundError:
            raise DDNSUpdateFailed(msg="DDNS key not found, cannot update DNS")
        keyfile = f.read()
        f.close()
        hostname = re.search(r'key \"(.*)\"', keyfile).group(1)
        self.algo = re.search(r'algorithm (.*);', keyfile).group(1)
        key = re.search(r'secret \"(.*)\";', keyfile).group(1)
        k = {hostname: key}
        try:
            self.keyring = dns.tsigkeyring.from_text(k)
        except DNSException:
            raise DDNSUpdateFailed(msg='{} is not a valid key file. The file should be in DNS KEY record format. See dnssec-keygen(8)'.format(self.keyfile))

    def _is_valid_v4addr(self, address):
        try:
            dns.ipv4.inet_aton(address)
        except socket.error:
            log.exception('{} is not a valid IPv4 address'.format(address))
            return False
        return True

    def _is_valid_v6addr(self, address):
        try:
            dns.ipv6.inet_aton(address)
        except SyntaxError:
            log.exception('{} is not a valid IPv6 address'.format(address))
            return False
        return True

    def _is_valid_name(self, name):
        try:
            dns.name.from_text(name)
        except DNSException:
            log.error('{} is not a valid DNS name'.format(name))
            return False
        return True

    def _parse_name(self, name):
        n = dns.name.from_text(name)
        origin = dns.resolver.zone_for_name(n)
        name = n.relativize(origin)
        return origin, name

    def _prep_ptr(self, ip):
        reversename = dns.reversename.from_address(ip)
        ptr_origin, ptr_name = self._parse_name(str(reversename))
        ptr_update = dns.update.Update(ptr_origin, keyring=self.keyring)
        return ptr_update, ptr_name

    def _add_ptr(self, fqdn, ip):
        ptr_update, ptr_name = self._prep_ptr(ip)
        ptr_update.add(ptr_name, self.ttl, 'PTR', fqdn + ".")
        self._do_update(ptr_update)

    def _update_ptr(self, fqdn, ip):
        ptr_update, ptr_name = self._prep_ptr(ip)
        ptr_update.replace(ptr_name, self.ttl, 'PTR', fqdn + ".")
        self._do_update(ptr_update)

    def _del_ptr(self, fqdn, ip):
        ptr_update, ptr_name = self._prep_ptr(ip)
        ptr_update.delete(ptr_name)
        self._do_update(ptr_update)

    def add_a_record(self, hostname, ip, do_ptr=True):
        fqdn = self._get_fqdn(hostname)
        if not self._is_valid_v4addr(ip):
            return
        if not self._is_valid_name(fqdn):
            return
        self._add_record("A", fqdn, ip, do_ptr)

    def add_aaaa_record(self, hostname, ip, do_ptr=True):
        fqdn = self._get_fqdn(hostname)
        if not self._is_valid_v6addr(ip):
            return
        if not self._is_valid_name(fqdn):
            return
        self._add_record("AAAA", fqdn, ip, do_ptr)

    def _add_record(self, qtype, fqdn, ip, do_ptr):
        log.debug('DDNS add for record {}, fqdn: {}'.format(qtype, fqdn))
        origin, name = self._parse_name(fqdn)
        update = dns.update.Update(origin, keyring=self.keyring)
        update.add(name, self.ttl, qtype, ip)
        self._do_update(update)
        if do_ptr:
            self._add_ptr(fqdn, ip)

    def _update_record(self, qtype, fqdn, data, do_ptr):
        log.debug('DDNS update for record {}, fqdn: {}'.format(qtype, fqdn))
        origin, name = self._parse_name(fqdn)
        update = dns.update.Update(origin, keyring=self.keyring)
        update.replace(name, self.ttl, qtype, data)
        self._do_update(update)
        if do_ptr:
            self._update_ptr(fqdn, data)

    def delete_a_record(self, hostname, ip, do_ptr=True):
        fqdn = self._get_fqdn(hostname)
        if not self._is_valid_v4addr(ip):
            return
        if not self._is_valid_name(fqdn):
            return
        self._delete_record("A", fqdn, ip, do_ptr)

    def _delete_record(self, qtype, fqdn, data, do_ptr):
        log.debug('DDNS delete for record {}, fqdn: {}'.format(qtype, fqdn))
        origin, name = self._parse_name(fqdn)
        update = dns.update.Update(origin, keyring=self.keyring)
        update.delete(name)
        self._do_update(update)
        if do_ptr:
            self._del_ptr(fqdn, data)

    def _do_update(self, update):
        try:
            response = dns.query.tcp(update, self.server)
        except dns.tsig.PeerBadKey:
            log.error('the server is refusing our key')
            return
        except dns.tsig.PeerBadSignature:
            log.error('something is wrong with the signature of the key')
            return
        if response.rcode() != dns.rcode.NOERROR:
            log.error('DDNS update resulted in: {}'.format(dns.rcode.to_text(response.rcode())))

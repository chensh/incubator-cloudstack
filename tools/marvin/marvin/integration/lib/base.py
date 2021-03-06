# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

""" Base class for all Cloudstack resources
    -Virtual machine, Volume, Snapshot etc
"""

import marvin
from utils import is_server_ssh_ready, random_gen
from marvin.cloudstackAPI import *
#Import System modules
import time
import hashlib
import base64


class Domain:
    """ Domain Life Cycle """
    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, name=None, networkdomain=None,
               parentdomainid=None):
        """Creates an domain"""

        cmd = createDomain.createDomainCmd()

        if name:
            cmd.name = "-".join([name, random_gen()])
        elif "name" in services:
            cmd.name = "-".join([services["name"], random_gen()])

        if networkdomain:
            cmd.networkdomain = networkdomain
        elif "networkdomain" in services:
            cmd.networkdomain = services["networkdomain"]

        if parentdomainid:
            cmd.parentdomainid = parentdomainid
        elif "parentdomainid" in services:
            cmd.parentdomainid = services["parentdomainid"]

        return Domain(apiclient.createDomain(cmd).__dict__)

    def delete(self, apiclient, cleanup=None):
        """Delete an domain"""
        cmd = deleteDomain.deleteDomainCmd()
        cmd.id = self.id
        if cleanup:
            cmd.cleanup = cleanup
        apiclient.deleteDomain(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists domains"""
        cmd = listDomains.listDomainsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listDomains(cmd))


class Account:
    """ Account Life Cycle """
    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, admin=False, domainid=None):
        """Creates an account"""
        cmd = createAccount.createAccountCmd()

        #0 - User, 1 - Root Admin, 2 - Domain Admin
        cmd.accounttype = 2 if (admin and domainid) else int(admin)

        cmd.email = services["email"]
        cmd.firstname = services["firstname"]
        cmd.lastname = services["lastname"]

        # Password Encoding
        mdf = hashlib.md5()
        mdf.update(services["password"])
        cmd.password = mdf.hexdigest()
        cmd.username = "-".join([services["username"], random_gen()])

        if domainid:
            cmd.domainid = domainid
        account = apiclient.createAccount(cmd)

        return Account(account.__dict__)

    def delete(self, apiclient):
        """Delete an account"""
        cmd = deleteAccount.deleteAccountCmd()
        cmd.id = self.account.id
        apiclient.deleteAccount(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists accounts and provides detailed account information for
        listed accounts"""

        cmd = listAccounts.listAccountsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listAccounts(cmd))


class User:
    """ User Life Cycle """
    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, account, domainid):
        cmd = createUser.createUserCmd()
        """Creates an user"""

        cmd.account = account
        cmd.domainid = domainid
        cmd.email = services["email"]
        cmd.firstname = services["firstname"]
        cmd.lastname = services["lastname"]

        # Password Encoding
        mdf = hashlib.md5()
        mdf.update(services["password"])
        cmd.password = mdf.hexdigest()
        cmd.username = "-".join([services["username"], random_gen()])
        user = apiclient.createUser(cmd)

        return User(user.__dict__)

    def delete(self, apiclient):
        """Delete an account"""
        cmd = deleteUser.deleteUserCmd()
        cmd.id = self.id
        apiclient.deleteUser(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists users and provides detailed account information for
        listed users"""

        cmd = listUsers.listUsersCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listUsers(cmd))

    @classmethod
    def registerUserKeys(cls, apiclient, userid):
        cmd = registerUserKeys.registerUserKeysCmd()
        cmd.id = userid
        return apiclient.registerUserKeys(cmd)

    def update(self, apiclient, **kwargs):
        """Updates the user details"""

        cmd = updateUser.updateUserCmd()
        cmd.id = self.id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return (apiclient.updateUser(cmd))

    @classmethod
    def update(cls, apiclient, id, **kwargs):
        """Updates the user details (class method)"""

        cmd = updateUser.updateUserCmd()
        cmd.id = id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return (apiclient.updateUser(cmd))

    @classmethod
    def login(cls, apiclient, username, password, domain=None, domainid=None):
        """Logins to the CloudStack"""

        cmd = login.loginCmd()
        cmd.username = username
        # MD5 hashcoded password
        mdf = hashlib.md5()
        mdf.update(password)
        cmd.password = mdf.hexdigest()
        if domain:
            cmd.domain = domain
        if domainid:
            cmd.domainid = domainid
        return apiclient.login(cmd)


class VirtualMachine:
    """Manage virtual machine lifecycle"""

    def __init__(self, items, services):
        self.__dict__.update(items)
        if "username" in services:
            self.username = services["username"]
        else:
            self.username = 'root'
        if "password" in services:
            self.password = services["password"]
        else:
            self.password = 'password'
        if "ssh_port" in services:
            self.ssh_port = services["ssh_port"]
        else:
            self.ssh_port = 22
        self.ssh_client = None
        #extract out the ipaddress
        self.ipaddress = self.nic[0].ipaddress

    @classmethod
    def create(cls, apiclient, services, templateid=None, accountid=None,
                    domainid=None, zoneid=None, networkids=None, serviceofferingid=None,
                    securitygroupids=None, projectid=None, startvm=None,
                    diskofferingid=None, hostid=None, mode='basic'):
        """Create the instance"""

        cmd = deployVirtualMachine.deployVirtualMachineCmd()

        if serviceofferingid:
            cmd.serviceofferingid = serviceofferingid
        elif "serviceoffering" in services:
            cmd.serviceofferingid = services["serviceoffering"]

        if zoneid:
            cmd.zoneid = zoneid
        elif "zoneid" in services:
            cmd.zoneid = services["zoneid"]
        cmd.hypervisor = services["hypervisor"]

        if accountid:
            cmd.account = accountid
        elif "account" in services:
            cmd.account = services["account"]

        if domainid:
            cmd.domainid = domainid
        elif "domainid" in services:
            cmd.domainid = services["domainid"]

        if networkids:
            cmd.networkids = networkids
        elif "networkids" in services:
            cmd.networkids = services["networkids"]

        if templateid:
            cmd.templateid = templateid
        elif "template" in services:
            cmd.templateid = services["template"]

        if "diskoffering" in services:
            cmd.diskofferingid = services["diskoffering"]

        if securitygroupids:
            cmd.securitygroupids = [str(sg_id) for sg_id in securitygroupids]

        if "userdata" in services:
            cmd.userdata = base64.b64encode(services["userdata"])

        if projectid:
            cmd.projectid = projectid

        if startvm is not None:
            cmd.startvm = startvm

        if hostid:
            cmd.hostid = hostid

        virtual_machine = apiclient.deployVirtualMachine(cmd)

        # VM should be in Running state after deploy
        timeout = 10
        while True:
            vm_status = VirtualMachine.list(
                                            apiclient,
                                            id=virtual_machine.id
                                            )
            if isinstance(vm_status, list):
                if vm_status[0].state == 'Running':
                    break
                elif timeout == 0:
                    raise Exception(
                            "TimeOutException: Failed to start VM (ID: %s)" %
                                                        virtual_machine.id)

            time.sleep(10)
            timeout = timeout - 1

        if mode.lower() == 'advanced':
            public_ip = PublicIPAddress.create(
                                           apiclient,
                                           virtual_machine.account,
                                           virtual_machine.zoneid,
                                           virtual_machine.domainid,
                                           services
                                           )
            fw_rule = FireWallRule.create(
                                          apiclient,
                                          ipaddressid=public_ip.ipaddress.id,
                                          protocol='TCP',
                                          cidrlist=['0.0.0.0/0'],
                                          startport=22,
                                          endport=22
                            )
            nat_rule = NATRule.create(
                                    apiclient,
                                    virtual_machine,
                                    services,
                                    ipaddressid=public_ip.ipaddress.id
                                    )
            virtual_machine.ssh_ip = nat_rule.ipaddress
            virtual_machine.public_ip = nat_rule.ipaddress
        else:
            virtual_machine.ssh_ip = virtual_machine.nic[0].ipaddress
            virtual_machine.public_ip = virtual_machine.nic[0].ipaddress

        return VirtualMachine(virtual_machine.__dict__, services)

    def start(self, apiclient):
        """Start the instance"""
        cmd = startVirtualMachine.startVirtualMachineCmd()
        cmd.id = self.id
        apiclient.startVirtualMachine(cmd)

    def stop(self, apiclient):
        """Stop the instance"""
        cmd = stopVirtualMachine.stopVirtualMachineCmd()
        cmd.id = self.id
        apiclient.stopVirtualMachine(cmd)

    def reboot(self, apiclient):
        """Reboot the instance"""
        cmd = rebootVirtualMachine.rebootVirtualMachineCmd()
        cmd.id = self.id
        apiclient.rebootVirtualMachine(cmd)

    def get_ssh_client(self, ipaddress=None, reconnect=False, port=None):
        """Get SSH object of VM"""

        # If NAT Rules are not created while VM deployment in Advanced mode
        # then, IP address must be passed
        if ipaddress != None:
            self.ssh_ip = ipaddress
        if port:
            self.ssh_port = port

        if reconnect:
            self.ssh_client = is_server_ssh_ready(
                                                    self.ssh_ip,
                                                    self.ssh_port,
                                                    self.username,
                                                    self.password
                                                )
        self.ssh_client = self.ssh_client or is_server_ssh_ready(
                                                    self.ssh_ip,
                                                    self.ssh_port,
                                                    self.username,
                                                    self.password
                                                )
        return self.ssh_client

    def delete(self, apiclient):
        """Destroy an Instance"""
        cmd = destroyVirtualMachine.destroyVirtualMachineCmd()
        cmd.id = self.id
        apiclient.destroyVirtualMachine(cmd)

    def attach_volume(self, apiclient, volume):
        """Attach volume to instance"""
        cmd = attachVolume.attachVolumeCmd()
        cmd.id = volume.id
        cmd.virtualmachineid = self.id
        return apiclient.attachVolume(cmd)

    def detach_volume(self, apiclient, volume):
        """Detach volume to instance"""
        cmd = detachVolume.detachVolumeCmd()
        cmd.id = volume.id
        return apiclient.detachVolume(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all VMs matching criteria"""

        cmd = listVirtualMachines.listVirtualMachinesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listVirtualMachines(cmd))

    def resetPassword(self, apiclient):
        """Resets VM password if VM created using password enabled template"""

        cmd = resetPasswordForVirtualMachine.resetPasswordForVirtualMachineCmd()
        cmd.id = self.id
        try:
            response = apiclient.resetPasswordForVirtualMachine(cmd)
            print response
        except Exception as e:
            raise Exception("Reset Password failed! - %s" % e)
        print type(response)
        if isinstance(response, list):
            return response[0].password


class Volume:
    """Manage Volume Lifecycle
    """
    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, zoneid=None, account=None,
               domainid=None, diskofferingid=None, projectid=None):
        """Create Volume"""
        cmd = createVolume.createVolumeCmd()
        cmd.name = services["diskname"]

        if diskofferingid:
            cmd.diskofferingid = diskofferingid
        elif "diskofferingid" in services:
            cmd.diskofferingid = services["diskofferingid"]

        if zoneid:
            cmd.zoneid = zoneid
        elif "zoneid" in services:
            cmd.zoneid = services["zoneid"]

        if account:
            cmd.account = account
        elif "account" in services:
            cmd.account = services["account"]

        if domainid:
            cmd.domainid = domainid
        elif "domainid" in services:
            cmd.domainid = services["domainid"]

        if projectid:
            cmd.projectid = projectid
        return Volume(apiclient.createVolume(cmd).__dict__)

    @classmethod
    def create_custom_disk(cls, apiclient, services, account=None,
                                    domainid=None, diskofferingid=None):
        """Create Volume from Custom disk offering"""
        cmd = createVolume.createVolumeCmd()
        cmd.name = services["diskname"]

        if diskofferingid:
            cmd.diskofferingid = diskofferingid
        elif "customdiskofferingid" in services:
            cmd.diskofferingid = services["customdiskofferingid"]

        cmd.size = services["customdisksize"]
        cmd.zoneid = services["zoneid"]

        if account:
            cmd.account = account
        else:
            cmd.account = services["account"]

        if domainid:
            cmd.domainid = domainid
        else:
            cmd.domainid = services["domainid"]

        return Volume(apiclient.createVolume(cmd).__dict__)

    @classmethod
    def create_from_snapshot(cls, apiclient, snapshot_id, services,
                             account=None, domainid=None):
        """Create Volume from snapshot"""
        cmd = createVolume.createVolumeCmd()
        cmd.name = "-".join([services["diskname"], random_gen()])
        cmd.snapshotid = snapshot_id
        cmd.zoneid = services["zoneid"]
        cmd.size = services["size"]
        if account:
            cmd.account = account
        else:
            cmd.account = services["account"]
        if domainid:
            cmd.domainid = domainid
        else:
            cmd.domainid = services["domainid"]
        return Volume(apiclient.createVolume(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Volume"""
        cmd = deleteVolume.deleteVolumeCmd()
        cmd.id = self.id
        apiclient.deleteVolume(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all volumes matching criteria"""

        cmd = listVolumes.listVolumesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listVolumes(cmd))

    def resize(cls, apiclient, **kwargs):
        """Resize a volume"""
        cmd = resizeVolume.resizeVolumeCmd()
        cmd.id = self.id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.resizeVolume(cmd))

class Snapshot:
    """Manage Snapshot Lifecycle
    """
    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, volume_id, account=None,
                                            domainid=None, projectid=None):
        """Create Snapshot"""
        cmd = createSnapshot.createSnapshotCmd()
        cmd.volumeid = volume_id
        if account:
            cmd.account = account
        if domainid:
            cmd.domainid = domainid
        if projectid:
            cmd.projectid = projectid
        return Snapshot(apiclient.createSnapshot(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Snapshot"""
        cmd = deleteSnapshot.deleteSnapshotCmd()
        cmd.id = self.id
        apiclient.deleteSnapshot(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all snapshots matching criteria"""

        cmd = listSnapshots.listSnapshotsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listSnapshots(cmd))


class Template:
    """Manage template life cycle"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, volumeid=None,
               account=None, domainid=None, projectid=None):
        """Create template from Volume"""
        #Create template from Virtual machine and Volume ID
        cmd = createTemplate.createTemplateCmd()
        cmd.displaytext = services["displaytext"]
        cmd.name = "-".join([services["name"], random_gen()])
        if "ostypeid" in services:
            cmd.ostypeid = services["ostypeid"]
        elif "ostype" in services:
            # Find OSTypeId from Os type
            sub_cmd = listOsTypes.listOsTypesCmd()
            sub_cmd.description = services["ostype"]
            ostypes = apiclient.listOsTypes(sub_cmd)

            if not isinstance(ostypes, list):
                raise Exception(
                    "Unable to find Ostype id with desc: %s" %
                                                services["ostype"])
            cmd.ostypeid = ostypes[0].id
        else:
            raise Exception(
                    "Unable to find Ostype is required for creating template")

        cmd.isfeatured = services["isfeatured"] if "isfeatured" in services else False
        cmd.ispublic = services["ispublic"] if "ispublic" in services else False
        cmd.isextractable = services["isextractable"] if "isextractable" in services else False
        cmd.passwordenabled = services["passwordenabled"] if "passwordenabled" in services else False
        cmd.passwordenabled = services["passwordenabled"] if "passwordenabled" in services else False

        if volumeid:
            cmd.volumeid = volumeid

        if account:
            cmd.account = account

        if domainid:
            cmd.domainid = domainid

        if projectid:
            cmd.projectid = projectid
        return Template(apiclient.createTemplate(cmd).__dict__)

    @classmethod
    def register(cls, apiclient, services, zoneid=None,
                                                account=None, domainid=None):
        """Create template from URL"""

        #Create template from Virtual machine and Volume ID
        cmd = registerTemplate.registerTemplateCmd()
        cmd.displaytext = services["displaytext"]
        cmd.name = "-".join([services["name"], random_gen()])
        cmd.format = services["format"]
        cmd.hypervisor = services["hypervisor"]

        if "ostypeid" in services:
            cmd.ostypeid = services["ostypeid"]
        elif "ostype" in services:
            # Find OSTypeId from Os type
            sub_cmd = listOsTypes.listOsTypesCmd()
            sub_cmd.description = services["ostype"]
            ostypes = apiclient.listOsTypes(sub_cmd)

            if not isinstance(ostypes, list):
                raise Exception(
                    "Unable to find Ostype id with desc: %s" %
                                                services["ostype"])
            cmd.ostypeid = ostypes[0].id
        else:
            raise Exception(
                    "Unable to find Ostype is required for registering template")

        cmd.url = services["url"]

        if zoneid:
            cmd.zoneid = zoneid
        else:
            cmd.zoneid = services["zoneid"]

        cmd.isfeatured = services["isfeatured"] if "isfeatured" in services else False
        cmd.ispublic = services["ispublic"] if "ispublic" in services else False
        cmd.isextractable = services["isextractable"] if "isextractable" in services else False
        cmd.passwordenabled = services["passwordenabled"] if "passwordenabled" in services else False

        if account:
            cmd.account = account

        if domainid:
            cmd.domainid = domainid

        # Register Template
        template = apiclient.registerTemplate(cmd)

        if isinstance(template, list):
            return Template(template[0].__dict__)

    @classmethod
    def create_from_snapshot(cls, apiclient, snapshot, services,
                                                        random_name=True):
        """Create Template from snapshot"""
        #Create template from Virtual machine and Snapshot ID
        cmd = createTemplate.createTemplateCmd()
        cmd.displaytext = services["displaytext"]
        cmd.name = "-".join([
                             services["name"],
                             random_gen()
                            ]) if random_name else services["name"]

        if "ostypeid" in services:
            cmd.ostypeid = services["ostypeid"]
        elif "ostype" in services:
            # Find OSTypeId from Os type
            sub_cmd = listOsTypes.listOsTypesCmd()
            sub_cmd.description = services["ostype"]
            ostypes = apiclient.listOsTypes(sub_cmd)

            if not isinstance(ostypes, list):
                raise Exception(
                    "Unable to find Ostype id with desc: %s" %
                                                services["ostype"])
            cmd.ostypeid = ostypes[0].id
        else:
            raise Exception(
                    "Unable to find Ostype is required for creating template")

        cmd.snapshotid = snapshot.id
        return Template(apiclient.createTemplate(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Template"""

        cmd = deleteTemplate.deleteTemplateCmd()
        cmd.id = self.id
        apiclient.deleteTemplate(cmd)

    def download(self, apiclient, timeout=5, interval=60):
        """Download Template"""
        #Sleep to ensure template is in proper state before download
        time.sleep(interval)

        while True:
            template_response = Template.list(
                                    apiclient,
                                    id=self.id,
                                    zoneid=self.zoneid,
                                    templatefilter='self'
                                    )
            if isinstance(template_response, list):

                template = template_response[0]
                # If template is ready,
                # template.status = Download Complete
                # Downloading - x% Downloaded
                # Error - Any other string
                if template.status == 'Download Complete':
                    break

                elif 'Downloaded' in template.status:
                    time.sleep(interval)

                elif 'Installing' not in template.status:
                    raise Exception(
                        "Error in downloading template: status - %s" %
                                                            template.status)

            elif timeout == 0:
                break

            else:
                time.sleep(interval)
                timeout = timeout - 1
        return

    def updatePermissions(self, apiclient, **kwargs):
        """Updates the template permissions"""

        cmd = updateTemplatePermissions.updateTemplatePermissionsCmd()
        cmd.id = self.id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.updateTemplatePermissions(cmd))

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all templates matching criteria"""

        cmd = listTemplates.listTemplatesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listTemplates(cmd))


class Iso:
    """Manage ISO life cycle"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, account=None, domainid=None,
                                                        projectid=None):
        """Create an ISO"""
        #Create ISO from URL
        cmd = registerIso.registerIsoCmd()
        cmd.displaytext = services["displaytext"]
        cmd.name = services["name"]
        if "ostypeid" in services:
            cmd.ostypeid = services["ostypeid"]
        elif "ostype" in services:
            # Find OSTypeId from Os type
            sub_cmd = listOsTypes.listOsTypesCmd()
            sub_cmd.description = services["ostype"]
            ostypes = apiclient.listOsTypes(sub_cmd)

            if not isinstance(ostypes, list):
                raise Exception(
                    "Unable to find Ostype id with desc: %s" %
                                                services["ostype"])
            cmd.ostypeid = ostypes[0].id
        else:
            raise Exception(
                    "Unable to find Ostype is required for creating ISO")

        cmd.url = services["url"]
        cmd.zoneid = services["zoneid"]

        if "isextractable" in services:
            cmd.isextractable = services["isextractable"]
        if "isfeatured" in services:
            cmd.isfeatured = services["isfeatured"]
        if "ispublic" in services:
            cmd.ispublic = services["ispublic"]

        if account:
            cmd.account = account
        if domainid:
            cmd.domainid = domainid
        if projectid:
            cmd.projectid = projectid
        # Register ISO
        iso = apiclient.registerIso(cmd)

        if iso:
            return Iso(iso[0].__dict__)

    def delete(self, apiclient):
        """Delete an ISO"""
        cmd = deleteIso.deleteIsoCmd()
        cmd.id = self.id
        apiclient.deleteIso(cmd)
        return

    def download(self, apiclient, timeout=5, interval=60):
        """Download an ISO"""
        #Ensuring ISO is successfully downloaded
        while True:
            time.sleep(interval)

            cmd = listIsos.listIsosCmd()
            cmd.id = self.id
            iso_response = apiclient.listIsos(cmd)

            if isinstance(iso_response, list):
                response = iso_response[0]
                # Again initialize timeout to avoid listISO failure
                timeout = 5
                print response.status
                # Check whether download is in progress(for Ex:10% Downloaded)
                # or ISO is 'Successfully Installed'
                if response.status == 'Successfully Installed':
                    return
                elif 'Downloaded' not in response.status and \
                    'Installing' not in response.status:
                    raise Exception(
                        "Error In Downloading ISO: ISO Status - %s" %
                                                            response.status)

            elif timeout == 0:
                raise Exception("ISO download Timeout Exception")
            else:
                timeout = timeout - 1
        return

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists all available ISO files."""

        cmd = listIsos.listIsosCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listIsos(cmd))


class PublicIPAddress:
    """Manage Public IP Addresses"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, accountid=None, zoneid=None, domainid=None,
               services=None, networkid=None, projectid=None, vpcid=None):
        """Associate Public IP address"""
        cmd = associateIpAddress.associateIpAddressCmd()

        if accountid:
            cmd.account = accountid

        if zoneid:
            cmd.zoneid = zoneid
        elif "zoneid" in services:
            cmd.zoneid = services["zoneid"]

        if domainid:
            cmd.domainid = domainid
        elif "domainid" in services:
            cmd.domainid = services["domainid"]

        if networkid:
            cmd.networkid = networkid

        if projectid:
            cmd.projectid = projectid

        if vpcid:
            cmd.vpcid = vpcid
        return PublicIPAddress(apiclient.associateIpAddress(cmd).__dict__)

    def delete(self, apiclient):
        """Dissociate Public IP address"""
        cmd = disassociateIpAddress.disassociateIpAddressCmd()
        cmd.id = self.ipaddress.id
        apiclient.disassociateIpAddress(cmd)
        return

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all Public IPs matching criteria"""

        cmd = listPublicIpAddresses.listPublicIpAddressesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listPublicIpAddresses(cmd))


class NATRule:
    """Manage port forwarding rule"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, virtual_machine, services, ipaddressid=None,
                                                            projectid=None, networkid=None):
        """Create Port forwarding rule"""
        cmd = createPortForwardingRule.createPortForwardingRuleCmd()

        if ipaddressid:
            cmd.ipaddressid = ipaddressid
        elif "ipaddressid" in services:
            cmd.ipaddressid = services["ipaddressid"]

        cmd.privateport = services["privateport"]
        cmd.publicport = services["publicport"]
        cmd.protocol = services["protocol"]
        cmd.virtualmachineid = virtual_machine.id

        if projectid:
            cmd.projectid = projectid

        if networkid:
            cmd.networkid = networkid

        return NATRule(apiclient.createPortForwardingRule(cmd).__dict__)

    def delete(self, apiclient):
        """Delete port forwarding"""
        cmd = deletePortForwardingRule.deletePortForwardingRuleCmd()
        cmd.id = self.id
        apiclient.deletePortForwardingRule(cmd)
        return

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all NAT rules matching criteria"""

        cmd = listPortForwardingRules.listPortForwardingRulesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listPortForwardingRules(cmd))


class StaticNATRule:
    """Manage Static NAT rule"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, ipaddressid=None, vpcid=None):
        """Creates static ip forwarding rule"""

        cmd = createIpForwardingRule.createIpForwardingRuleCmd()
        cmd.protocol = services["protocol"]
        cmd.startport = services["startport"]

        if "endport" in services:
            cmd.endport = services["endport"]

        if "cidrlist" in services:
            cmd.cidrlist = services["cidrlist"]

        if ipaddressid:
            cmd.ipaddressid = ipaddressid
        elif "ipaddressid" in services:
            cmd.ipaddressid = services["ipaddressid"]

        if vpcid:
            cmd.vpcid = vpcid

        return StaticNATRule(apiclient.createIpForwardingRule(cmd).__dict__)

    def delete(self, apiclient):
        """Delete IP forwarding rule"""
        cmd = deleteIpForwardingRule.deleteIpForwardingRuleCmd()
        cmd.id = self.id
        apiclient.deleteIpForwardingRule(cmd)
        return

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all IP forwarding rules matching criteria"""

        cmd = listIpForwardingRules.listIpForwardingRulesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listIpForwardingRules(cmd))

    @classmethod
    def enable(cls, apiclient, ipaddressid, virtualmachineid):
        """Enables Static NAT rule"""

        cmd = enableStaticNat.enableStaticNatCmd()
        cmd.ipaddressid = ipaddressid
        cmd.virtualmachineid = virtualmachineid
        apiclient.enableStaticNat(cmd)
        return

    @classmethod
    def disable(cls, apiclient, ipaddressid, virtualmachineid):
        """Disables Static NAT rule"""

        cmd = disableStaticNat.disableStaticNatCmd()
        cmd.ipaddressid = ipaddressid
        apiclient.disableStaticNat(cmd)
        return


class FireWallRule:
    """Manage Firewall rule"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, ipaddressid, protocol, cidrlist=None,
               startport=None, endport=None, projectid=None, vpcid=None):
        """Create Firewall Rule"""
        cmd = createFirewallRule.createFirewallRuleCmd()
        cmd.ipaddressid = ipaddressid
        cmd.protocol = protocol
        if cidrlist:
            cmd.cidrlist = cidrlist
        if startport:
            cmd.startport = startport
        if endport:
            cmd.endport = endport

        if projectid:
            cmd.projectid = projectid

        if vpcid:
            cmd.vpcid = vpcid

        return FireWallRule(apiclient.createFirewallRule(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Firewall rule"""
        cmd = deleteFirewallRule.deleteFirewallRuleCmd()
        cmd.id = self.id
        apiclient.deleteFirewallRule(cmd)
        return

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all Firewall Rules matching criteria"""

        cmd = listFirewallRules.listFirewallRulesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listFirewallRules(cmd))


class ServiceOffering:
    """Manage service offerings cycle"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, domainid=None, **kwargs):
        """Create Service offering"""
        cmd = createServiceOffering.createServiceOfferingCmd()
        cmd.cpunumber = services["cpunumber"]
        cmd.cpuspeed = services["cpuspeed"]
        cmd.displaytext = services["displaytext"]
        cmd.memory = services["memory"]
        cmd.name = services["name"]
        if "storagetype" in services:
            cmd.storagetype = services["storagetype"]

        # Service Offering private to that domain
        if domainid:
            cmd.domainid = domainid

        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return ServiceOffering(apiclient.createServiceOffering(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Service offering"""
        cmd = deleteServiceOffering.deleteServiceOfferingCmd()
        cmd.id = self.id
        apiclient.deleteServiceOffering(cmd)
        return

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists all available service offerings."""

        cmd = listServiceOfferings.listServiceOfferingsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listServiceOfferings(cmd))


class DiskOffering:
    """Manage disk offerings cycle"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, custom=False, domainid=None):
        """Create Disk offering"""
        cmd = createDiskOffering.createDiskOfferingCmd()
        cmd.displaytext = services["displaytext"]
        cmd.name = services["name"]
        if custom:
            cmd.customized = True
        else:
            cmd.disksize = services["disksize"]

        if domainid:
            cmd.domainid = domainid

        if services["storagetype"]:
            cmd.storagetype = services["storagetype"]

        return DiskOffering(apiclient.createDiskOffering(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Disk offering"""
        cmd = deleteDiskOffering.deleteDiskOfferingCmd()
        cmd.id = self.id
        apiclient.deleteDiskOffering(cmd)
        return

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists all available disk offerings."""

        cmd = listDiskOfferings.listDiskOfferingsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listDiskOfferings(cmd))


class NetworkOffering:
    """Manage network offerings cycle"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, **kwargs):
        """Create network offering"""

        cmd = createNetworkOffering.createNetworkOfferingCmd()
        cmd.displaytext = "-".join([services["displaytext"], random_gen()])
        cmd.name = "-".join([services["name"], random_gen()])
        cmd.guestiptype = services["guestiptype"]
        cmd.supportedservices = services["supportedservices"]
        cmd.traffictype = services["traffictype"]

        cmd.serviceProviderList = []
        for service, provider in services["serviceProviderList"].items():
            cmd.serviceProviderList.append({
                                            'service': service,
                                            'provider': provider
                                           })
        if "servicecapabilitylist" in services:
            cmd.servicecapabilitylist = []
            for service, capability in services["servicecapabilitylist"].items():
                for ctype, value in capability.items():
                    cmd.servicecapabilitylist.append({
                                            'service': service,
                                            'capabilitytype': ctype,
                                            'capabilityvalue': value
                                           })
        if "specifyVlan" in services:
            cmd.specifyVlan = services["specifyVlan"]
        if "specifyIpRanges" in services:
            cmd.specifyIpRanges = services["specifyIpRanges"]

        [setattr(cmd, k, v) for k, v in kwargs.items()]

        return NetworkOffering(apiclient.createNetworkOffering(cmd).__dict__)

    def delete(self, apiclient):
        """Delete network offering"""
        cmd = deleteNetworkOffering.deleteNetworkOfferingCmd()
        cmd.id = self.id
        apiclient.deleteNetworkOffering(cmd)
        return

    def update(self, apiclient, **kwargs):
        """Lists all available network offerings."""

        cmd = updateNetworkOffering.updateNetworkOfferingCmd()
        cmd.id = self.id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.updateNetworkOffering(cmd))

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists all available network offerings."""

        cmd = listNetworkOfferings.listNetworkOfferingsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listNetworkOfferings(cmd))


class SnapshotPolicy:
    """Manage snapshot policies"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, volumeid, services):
        """Create Snapshot policy"""
        cmd = createSnapshotPolicy.createSnapshotPolicyCmd()
        cmd.intervaltype = services["intervaltype"]
        cmd.maxsnaps = services["maxsnaps"]
        cmd.schedule = services["schedule"]
        cmd.timezone = services["timezone"]
        cmd.volumeid = volumeid
        return SnapshotPolicy(apiclient.createSnapshotPolicy(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Snapshot policy"""
        cmd = deleteSnapshotPolicies.deleteSnapshotPoliciesCmd()
        cmd.id = self.id
        apiclient.deleteSnapshotPolicies(cmd)
        return

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists snapshot policies."""

        cmd = listSnapshotPolicies.listSnapshotPoliciesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listSnapshotPolicies(cmd))


class LoadBalancerRule:
    """Manage Load Balancer rule"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, ipaddressid=None, accountid=None,
                            networkid=None, projectid=None, domainid=None):
        """Create Load balancing Rule"""

        cmd = createLoadBalancerRule.createLoadBalancerRuleCmd()

        if ipaddressid:
            cmd.publicipid = ipaddressid
        elif "ipaddressid" in services:
            cmd.publicipid = services["ipaddressid"]

        if accountid:
            cmd.account = accountid
        elif "account" in services:
            cmd.account = services["account"]

        if domainid:
            cmd.domainid = domainid

        cmd.name = services["name"]
        cmd.algorithm = services["alg"]
        cmd.privateport = services["privateport"]
        cmd.publicport = services["publicport"]

        if "openfirewall" in services:
            cmd.openfirewall = services["openfirewall"]

        if projectid:
            cmd.projectid = projectid

        if networkid:
            cmd.networkid = networkid
        return LoadBalancerRule(apiclient.createLoadBalancerRule(cmd).__dict__)

    def delete(self, apiclient):
        """Delete load balancing rule"""
        cmd = deleteLoadBalancerRule.deleteLoadBalancerRuleCmd()
        cmd.id = self.id
        apiclient.deleteLoadBalancerRule(cmd)
        return

    def assign(self, apiclient, vms):
        """Assign virtual machines to load balancing rule"""
        cmd = assignToLoadBalancerRule.assignToLoadBalancerRuleCmd()
        cmd.id = self.id
        cmd.virtualmachineids = [str(vm.id) for vm in vms]
        apiclient.assignToLoadBalancerRule(cmd)
        return

    def remove(self, apiclient, vms):
        """Remove virtual machines from load balancing rule"""
        cmd = removeFromLoadBalancerRule.removeFromLoadBalancerRuleCmd()
        cmd.id = self.id
        cmd.virtualmachineids = [str(vm.id) for vm in vms]
        apiclient.removeFromLoadBalancerRule(cmd)
        return

    def update(self, apiclient, algorithm=None, description=None, name=None, **kwargs):
        """Updates the load balancing rule"""
        cmd = updateLoadBalancerRule.updateLoadBalancerRuleCmd()
        cmd.id = self.id
        if algorithm:
            cmd.algorithm = algorithm
        if description:
            cmd.description = description
        if name:
            cmd.name = name

        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return apiclient.updateLoadBalancerRule(cmd)

    def createSticky(self, apiclient, methodname, name, description=None, param=None):
        """Creates a sticky policy for the LB rule"""

        cmd = createLBStickinessPolicy.createLBStickinessPolicyCmd()
        cmd.lbruleid = self.id
        cmd.methodname = methodname
        cmd.name = name
        if description:
            cmd.description = description
        if param:
            cmd.param = []
            for name, value in param.items():
                cmd.param.append({'name': name, 'value': value})
        return apiclient.createLBStickinessPolicy(cmd)
    
    def deleteSticky(self, apiclient, id):
        """Deletes stickyness policy"""
        
        cmd = deleteLBStickinessPolicy.deleteLBStickinessPolicyCmd()
        cmd.id = id
        return apiclient.deleteLBStickinessPolicy(cmd)
    
    @classmethod
    def listStickyPolicies(cls, apiclient, lbruleid, **kwargs):
        """Lists stickiness policies for load balancing rule"""
        
        cmd= listLBStickinessPolicies.listLBStickinessPoliciesCmd()
        cmd.lbruleid = lbruleid
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return apiclient.listLBStickinessPolicies(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all Load balancing rules matching criteria"""

        cmd = listLoadBalancerRules.listLoadBalancerRulesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listLoadBalancerRules(cmd))


class Cluster:
    """Manage Cluster life cycle"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, zoneid=None, podid=None):
        """Create Cluster"""
        cmd = addCluster.addClusterCmd()
        cmd.clustertype = services["clustertype"]
        cmd.hypervisor = services["hypervisor"]

        if zoneid:
            cmd.zoneid = zoneid
        else:
            cmd.zoneid = services["zoneid"]

        if podid:
            cmd.podid = podid
        else:
            cmd.podid = services["podid"]

        if "username" in services:
            cmd.username = services["username"]
        if "password" in services:
            cmd.password = services["password"]
        if "url" in services:
            cmd.url = services["url"]
        if "clustername" in services:
            cmd.clustername = services["clustername"]

        return Cluster(apiclient.addCluster(cmd)[0].__dict__)

    def delete(self, apiclient):
        """Delete Cluster"""
        cmd = deleteCluster.deleteClusterCmd()
        cmd.id = self.id
        apiclient.deleteCluster(cmd)
        return

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all Clusters matching criteria"""

        cmd = listClusters.listClustersCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listClusters(cmd))


class Host:
    """Manage Host life cycle"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, cluster, services, zoneid=None, podid=None):
        """Create Host in cluster"""

        cmd = addHost.addHostCmd()
        cmd.hypervisor = services["hypervisor"]
        cmd.url = services["url"]
        cmd.clusterid = cluster.id

        if zoneid:
            cmd.zoneid = zoneid
        else:
            cmd.zoneid = services["zoneid"]

        if podid:
            cmd.podid = podid
        else:
            cmd.podid = services["podid"]

        if "clustertype" in services:
            cmd.clustertype = services["clustertype"]
        if "username" in services:
            cmd.username = services["username"]
        if "password" in services:
            cmd.password = services["password"]

        # Add host
        host = apiclient.addHost(cmd)

        if isinstance(host, list):
            return Host(host[0].__dict__)

    def delete(self, apiclient):
        """Delete Host"""
        # Host must be in maintenance mode before deletion
        cmd = prepareHostForMaintenance.prepareHostForMaintenanceCmd()
        cmd.id = self.id
        apiclient.prepareHostForMaintenance(cmd)
        time.sleep(30)

        cmd = deleteHost.deleteHostCmd()
        cmd.id = self.id
        apiclient.deleteHost(cmd)
        return

    def enableMaintenance(self, apiclient):
        """enables maintainance mode Host"""

        cmd = prepareHostForMaintenance.prepareHostForMaintenanceCmd()
        cmd.id = self.id
        return apiclient.prepareHostForMaintenance(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all Hosts matching criteria"""

        cmd = listHosts.listHostsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listHosts(cmd))


class StoragePool:
    """Manage Storage pools (Primary Storage)"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, clusterid=None,
                                        zoneid=None, podid=None):
        """Create Storage pool (Primary Storage)"""

        cmd = createStoragePool.createStoragePoolCmd()
        cmd.name = services["name"]

        if podid:
            cmd.podid = podid
        else:
            cmd.podid = services["podid"]

        cmd.url = services["url"]
        if clusterid:
            cmd.clusterid = clusterid
        elif "clusterid" in services:
            cmd.clusterid = services["clusterid"]

        if zoneid:
            cmd.zoneid = zoneid
        else:
            cmd.zoneid = services["zoneid"]

        return StoragePool(apiclient.createStoragePool(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Storage pool (Primary Storage)"""

        # Storage pool must be in maintenance mode before deletion
        cmd = enableStorageMaintenance.enableStorageMaintenanceCmd()
        cmd.id = self.id
        apiclient.enableStorageMaintenance(cmd)
        time.sleep(30)
        cmd = deleteStoragePool.deleteStoragePoolCmd()
        cmd.id = self.id
        apiclient.deleteStoragePool(cmd)
        return

    def enableMaintenance(self, apiclient):
        """enables maintainance mode Storage pool"""

        cmd = enableStorageMaintenance.enableStorageMaintenanceCmd()
        cmd.id = self.id
        return apiclient.enableStorageMaintenance(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all storage pools matching criteria"""

        cmd = listStoragePools.listStoragePoolsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listStoragePools(cmd))


class Network:
    """Manage Network pools"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, accountid=None, domainid=None,
               networkofferingid=None, projectid=None, zoneid=None,
               gateway=None, netmask=None, vpcid=None, guestcidr=None):
        """Create Network for account"""
        cmd = createNetwork.createNetworkCmd()
        cmd.name = services["name"]
        cmd.displaytext = services["displaytext"]

        if networkofferingid:
            cmd.networkofferingid = networkofferingid
        elif "networkoffering" in services:
            cmd.networkofferingid = services["networkoffering"]

        if zoneid:
            cmd.zoneid = zoneid
        elif "zoneid" in services:
            cmd.zoneid = services["zoneid"]

        if gateway:
            cmd.gateway = gateway
        elif "gateway" in services:
            cmd.gateway = services["gateway"]
        if netmask:
            cmd.netmask = netmask
        elif "netmask" in services:
            cmd.netmask = services["netmask"]
        if "startip" in services:
            cmd.startip = services["startip"]
        if "endip" in services:
            cmd.endip = services["endip"]
        if "vlan" in services:
            cmd.vlan = services["vlan"]
        if "acltype" in services:
            cmd.acltype = services["acltype"]

        if accountid:
            cmd.account = accountid
        if domainid:
            cmd.domainid = domainid
        if projectid:
            cmd.projectid = projectid
        if guestcidr:
            cmd.guestcidr = guestcidr
        if vpcid:
            cmd.vpcid = vpcid
        return Network(apiclient.createNetwork(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Account"""

        cmd = deleteNetwork.deleteNetworkCmd()
        cmd.id = self.id
        apiclient.deleteNetwork(cmd)

    def update(self, apiclient, **kwargs):
        """Updates network with parameters passed"""

        cmd = updateNetwork.updateNetworkCmd()
        cmd.id = self.id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.updateNetwork(cmd))

    def restart(self, apiclient, cleanup=None):
        """Restarts the network"""

        cmd = restartNetwork.restartNetworkCmd()
        cmd.id = self.id
        if cleanup:
            cmd.cleanup = cleanup
        return(apiclient.restartNetwork(cmd))

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all Networks matching criteria"""

        cmd = listNetworks.listNetworksCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listNetworks(cmd))


class NetworkACL:
    """Manage Network ACL lifecycle"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, networkid, services, traffictype=None):
        """Create network ACL rules(Ingress/Egress)"""

        cmd = createNetworkACL.createNetworkACLCmd()
        cmd.networkid = networkid
        if "protocol" in services:
            cmd.protocol = services["protocol"]

        if services["protocol"] == 'ICMP':
            cmd.icmptype = -1
            cmd.icmpcode = -1
        else:
            cmd.startport = services["startport"]
            cmd.endport = services["endport"]

        cmd.cidrlist = services["cidrlist"]
        if traffictype:
            cmd.traffictype = traffictype
            # Defaulted to Ingress
        return NetworkACL(apiclient.createNetworkACL(cmd).__dict__)

    def delete(self, apiclient):
        """Delete network acl"""

        cmd = deleteNetworkACL.deleteNetworkACLCmd()
        cmd.id = self.id
        return apiclient.deleteNetworkACL(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List Network ACLs"""

        cmd = listNetworkACLs.listNetworkACLsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listNetworkACLs(cmd))


class Vpn:
    """Manage VPN life cycle"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, publicipid, account=None, domainid=None,
                                                            projectid=None, vpcid=None):
        """Create VPN for Public IP address"""
        cmd = createRemoteAccessVpn.createRemoteAccessVpnCmd()
        cmd.publicipid = publicipid
        if account:
            cmd.account = account
        if domainid:
            cmd.domainid = domainid
        if projectid:
            cmd.projectid = projectid
        if vpcid:
            cmd.vpcid = vpcid
        return Vpn(apiclient.createRemoteAccessVpn(cmd).__dict__)

    def delete(self, apiclient):
        """Delete remote VPN access"""

        cmd = deleteRemoteAccessVpn.deleteRemoteAccessVpnCmd()
        cmd.publicipid = self.publicipid
        apiclient.deleteRemoteAccessVpn(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all VPN matching criteria"""

        cmd = listRemoteAccessVpns.listRemoteAccessVpnsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listRemoteAccessVpns(cmd))


class VpnUser:
    """Manage VPN user"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, username, password, account=None, domainid=None,
               projectid=None):
        """Create VPN user"""
        cmd = addVpnUser.addVpnUserCmd()
        cmd.username = username
        cmd.password = password

        if account:
            cmd.account = account
        if domainid:
            cmd.domainid = domainid
        if projectid:
            cmd.projectid = projectid
        return VpnUser(apiclient.addVpnUser(cmd).__dict__)

    def delete(self, apiclient):
        """Remove VPN user"""

        cmd = removeVpnUser.removeVpnUserCmd()
        cmd.username = self.username
        cmd.account = self.account
        cmd.domainid = self.domainid
        apiclient.removeVpnUser(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all VPN Users matching criteria"""

        cmd = listVpnUsers.listVpnUsersCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listVpnUsers(cmd))


class Zone:
    """Manage Zone"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, domainid=None):
        """Create zone"""
        cmd = createZone.createZoneCmd()
        cmd.dns1 = services["dns1"]
        cmd.internaldns1 = services["internaldns1"]
        cmd.name = services["name"]
        cmd.networktype = services["networktype"]

        if "dns2" in services:
            cmd.dns2 = services["dns2"]
        if "internaldns2" in services:
            cmd.internaldns2 = services["internaldns2"]
        if domainid:
            cmd.domainid = domainid

        return Zone(apiclient.createZone(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Zone"""

        cmd = deleteZone.deleteZoneCmd()
        cmd.id = self.id
        apiclient.deleteZone(cmd)

    def update(self, apiclient, **kwargs):
        """Update the zone"""

        cmd = updateZone.updateZoneCmd()
        cmd.id = self.id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return apiclient.updateZone(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List all Zones matching criteria"""

        cmd = listZones.listZonesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listZones(cmd))


class Pod:
    """Manage Pod"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services):
        """Create Pod"""
        cmd = createPod.createPodCmd()
        cmd.gateway = services["gateway"]
        cmd.netmask = services["netmask"]
        cmd.name = services["name"]
        cmd.startip = services["startip"]
        cmd.endip = services["endip"]
        cmd.zoneid = services["zoneid"]

        return Pod(apiclient.createPod(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Pod"""

        cmd = deletePod.deletePodCmd()
        cmd.id = self.id
        apiclient.deletePod(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        "Returns a default pod for specified zone"

        cmd = listPods.listPodsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return apiclient.listPods(cmd)


class PublicIpRange:
    """Manage VlanIpRange"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services):
        """Create VlanIpRange"""

        cmd = createVlanIpRange.createVlanIpRangeCmd()
        cmd.gateway = services["gateway"]
        cmd.netmask = services["netmask"]
        cmd.forvirtualnetwork = services["forvirtualnetwork"]
        cmd.startip = services["startip"]
        cmd.endip = services["endip"]
        cmd.zoneid = services["zoneid"]
        cmd.podid = services["podid"]
        cmd.vlan = services["vlan"]

        return PublicIpRange(apiclient.createVlanIpRange(cmd).__dict__)

    def delete(self, apiclient):
        """Delete VlanIpRange"""

        cmd = deleteVlanIpRange.deleteVlanIpRangeCmd()
        cmd.id = self.id
        apiclient.deleteVlanIpRange(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists all VLAN IP ranges."""

        cmd = listVlanIpRanges.listVlanIpRangesCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listVlanIpRanges(cmd))


class SecondaryStorage:
    """Manage Secondary storage"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services):
        """Create Secondary Storage"""
        cmd = addSecondaryStorage.addSecondaryStorageCmd()

        cmd.url = services["url"]
        if "zoneid" in services:
            cmd.zoneid = services["zoneid"]
        return SecondaryStorage(apiclient.addSecondaryStorage(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Secondary Storage"""

        cmd = deleteHost.deleteHostCmd()
        cmd.id = self.id
        apiclient.deleteHost(cmd)


class PhysicalNetwork:
    """Manage physical network storage"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, zoneid, domainid=None):
        """Create physical network"""
        cmd = createPhysicalNetwork.createPhysicalNetworkCmd()

        cmd.name = services["name"]
        cmd.zoneid = zoneid
        if domainid:
            cmd.domainid = domainid
        return PhysicalNetwork(apiclient.createPhysicalNetwork(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Physical Network"""

        cmd = deletePhysicalNetwork.deletePhysicalNetworkCmd()
        cmd.id = self.id
        apiclient.deletePhysicalNetwork(cmd)

    def update(self, apiclient, **kwargs):
        """Update Physical network state"""

        cmd = updatePhysicalNetwork.updatePhysicalNetworkCmd()
        cmd.id = self.id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return apiclient.updatePhysicalNetwork(cmd)

    def addTrafficType(self, apiclient, type):
        """Add Traffic type to Physical network"""

        cmd = addTrafficType.addTrafficTypeCmd()
        cmd.physicalnetworkid = self.id
        cmd.traffictype = type
        return apiclient.addTrafficType(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists all physical networks"""

        cmd = listPhysicalNetworks.listPhysicalNetworksCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listPhysicalNetworks(cmd))

class SecurityGroup:
    """Manage Security Groups"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, account=None, domainid=None,
               description=None, projectid=None):
        """Create security group"""
        cmd = createSecurityGroup.createSecurityGroupCmd()

        cmd.name = services["name"]
        if account:
            cmd.account = account
        if domainid:
            cmd.domainid = domainid
        if description:
            cmd.description = description
        if projectid:
            cmd.projectid = projectid

        return SecurityGroup(apiclient.createSecurityGroup(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Security Group"""

        cmd = deleteSecurityGroup.deleteSecurityGroupCmd()
        cmd.id = self.id
        apiclient.deleteSecurityGroup(cmd)

    def authorize(self, apiclient, services,
                  account=None, domainid=None, projectid=None):
        """Authorize Ingress Rule"""

        cmd = authorizeSecurityGroupIngress.authorizeSecurityGroupIngressCmd()

        if domainid:
            cmd.domainid = domainid
        if account:
            cmd.account = account

        if projectid:
            cmd.projectid = projectid
        cmd.securitygroupid = self.id
        cmd.protocol = services["protocol"]

        if services["protocol"] == 'ICMP':
            cmd.icmptype = -1
            cmd.icmpcode = -1
        else:
            cmd.startport = services["startport"]
            cmd.endport = services["endport"]

        cmd.cidrlist = services["cidrlist"]
        return (apiclient.authorizeSecurityGroupIngress(cmd).__dict__)

    def revoke(self, apiclient, id):
        """Revoke ingress rule"""

        cmd = revokeSecurityGroupIngress.revokeSecurityGroupIngressCmd()
        cmd.id = id
        return apiclient.revokeSecurityGroupIngress(cmd)

    def authorizeEgress(self, apiclient, services, account=None, domainid=None,
                        projectid=None, user_secgrp_list={}):
        """Authorize Egress Rule"""

        cmd = authorizeSecurityGroupEgress.authorizeSecurityGroupEgressCmd()

        if domainid:
            cmd.domainid = domainid
        if account:
            cmd.account = account

        if projectid:
            cmd.projectid = projectid
        cmd.securitygroupid = self.id
        cmd.protocol = services["protocol"]

        if services["protocol"] == 'ICMP':
            cmd.icmptype = -1
            cmd.icmpcode = -1
        else:
            cmd.startport = services["startport"]
            cmd.endport = services["endport"]

        cmd.cidrlist = services["cidrlist"]

        cmd.usersecuritygrouplist = []
        for account, group in user_secgrp_list.items():
            cmd.usersecuritygrouplist.append({
                                            'account': account,
                                            'group': group
                                           })

        return (apiclient.authorizeSecurityGroupEgress(cmd).__dict__)

    def revokeEgress(self, apiclient, id):
        """Revoke Egress rule"""

        cmd = revokeSecurityGroupEgress.revokeSecurityGroupEgressCmd()
        cmd.id = id
        return apiclient.revokeSecurityGroupEgress(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists all security groups."""

        cmd = listSecurityGroups.listSecurityGroupsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listSecurityGroups(cmd))


class Project:
    """Manage Project life cycle"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, account=None, domainid=None):
        """Create project"""

        cmd = createProject.createProjectCmd()
        cmd.displaytext = services["displaytext"]
        cmd.name = "-".join([services["name"], random_gen()])
        if account:
            cmd.account = account
        if domainid:
            cmd.domainid = domainid

        return Project(apiclient.createProject(cmd).__dict__)

    def delete(self, apiclient):
        """Delete Project"""

        cmd = deleteProject.deleteProjectCmd()
        cmd.id = self.id
        apiclient.deleteProject(cmd)

    def update(self, apiclient, **kwargs):
        """Updates the project"""

        cmd = updateProject.updateProjectCmd()
        cmd.id = self.id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return apiclient.updateProject(cmd)

    def activate(self, apiclient):
        """Activates the suspended project"""

        cmd = activateProject.activateProjectCmd()
        cmd.id = self.id
        return apiclient.activateProject(cmd)

    def suspend(self, apiclient):
        """Suspend the active project"""

        cmd = suspendProject.suspendProjectCmd()
        cmd.id = self.id
        return apiclient.suspendProject(cmd)

    def addAccount(self, apiclient, account=None, email=None):
        """Add account to project"""

        cmd = addAccountToProject.addAccountToProjectCmd()
        cmd.projectid = self.id
        if account:
            cmd.account = account
        if email:
            cmd.email = email
        return apiclient.addAccountToProject(cmd)

    def deleteAccount(self, apiclient, account):
        """Delete account from project"""

        cmd = deleteAccountFromProject.deleteAccountFromProjectCmd()
        cmd.projectid = self.id
        cmd.account = account
        return apiclient.deleteAccountFromProject(cmd)

    @classmethod
    def listAccounts(cls, apiclient, **kwargs):
        """Lists all accounts associated with projects."""

        cmd = listProjectAccounts.listProjectAccountsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listProjectAccounts(cmd))

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists all projects."""

        cmd = listProjects.listProjectsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listProjects(cmd))


class ProjectInvitation:
    """Manage project invitations"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def update(cls, apiclient, projectid, accept, account=None, token=None):
        """Updates the project invitation for that account"""

        cmd = updateProjectInvitation.updateProjectInvitationCmd()
        cmd.projectid = projectid
        cmd.accept = accept
        if account:
            cmd.account = account
        if token:
            cmd.token = token

        return (apiclient.updateProjectInvitation(cmd).__dict__)

    def delete(self, apiclient, id):
        """Deletes the project invitation"""

        cmd = deleteProjectInvitation.deleteProjectInvitationCmd()
        cmd.id = id
        return apiclient.deleteProjectInvitation(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists project invitations"""

        cmd = listProjectInvitations.listProjectInvitationsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listProjectInvitations(cmd))


class Configurations:
    """Manage Configuration"""

    @classmethod
    def update(cls, apiclient, name, value=None):
        """Updates the specified configuration"""

        cmd = updateConfiguration.updateConfigurationCmd()
        cmd.name = name
        cmd.value = value
        apiclient.updateConfiguration(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """Lists configurations"""

        cmd = listConfigurations.listConfigurationsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listConfigurations(cmd))


class NetScaler:
    """Manage external netscaler device"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def add(cls, apiclient, services, physicalnetworkid, username=None, password=None):
        """Add external netscaler device to cloudstack"""

        cmd = addNetscalerLoadBalancer.addNetscalerLoadBalancerCmd()
        cmd.physicalnetworkid = physicalnetworkid
        if username:
            cmd.username = username
        else:
            cmd.username = services["username"]

        if password:
            cmd.password = password
        else:
            cmd.password = services["password"]

        cmd.networkdevicetype = services["networkdevicetype"]

        # Generate the URL
        url = 'https://' + str(services["ipaddress"]) + '?'
        url = url + 'publicinterface=' + str(services["publicinterface"]) + '&'
        url = url + 'privateinterface=' + str(services["privateinterface"]) + '&'
        url = url + 'numretries=' + str(services["numretries"]) + '&'

        if not services["lbdevicededicated"] and "lbdevicecapacity" in services:
            url = url + 'lbdevicecapacity=' + str(services["lbdevicecapacity"]) + '&'

        url = url + 'lbdevicededicated=' + str(services["lbdevicededicated"])

        cmd.url = url
        return NetScaler(apiclient.addNetscalerLoadBalancer(cmd).__dict__)

    def delete(self, apiclient):
        """Deletes a netscaler device from CloudStack"""

        cmd = deleteNetscalerLoadBalancer.deleteNetscalerLoadBalancerCmd()
        cmd.lbdeviceid = self.lbdeviceid
        apiclient.deleteNetscalerLoadBalancer(cmd)
        return

    def configure(self, apiclient, **kwargs):
        """List already registered netscaler devices"""

        cmd = configureNetscalerLoadBalancer.configureNetscalerLoadBalancerCmd()
        cmd.lbdeviceid = self.lbdeviceid
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.configureNetscalerLoadBalancer(cmd))

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List already registered netscaler devices"""

        cmd = listNetscalerLoadBalancers.listNetscalerLoadBalancersCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listNetscalerLoadBalancers(cmd))


class NetworkServiceProvider:
    """Manage network serivce providers for CloudStack"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def add(cls, apiclient, name, physicalnetworkid, servicelist):
        """Adds network service provider"""

        cmd = addNetworkServiceProvider.addNetworkServiceProviderCmd()
        cmd.name = name
        cmd.physicalnetworkid = physicalnetworkid
        cmd.servicelist = servicelist
        return NetworkServiceProvider(apiclient.addNetworkServiceProvider(cmd).__dict__)

    def delete(self, apiclient):
        """Deletes network service provider"""

        cmd = deleteNetworkServiceProvider.deleteNetworkServiceProviderCmd()
        cmd.id = self.id
        return apiclient.deleteNetworkServiceProvider(cmd)

    def update(self, apiclient, **kwargs):
        """Updates network service provider"""

        cmd = updateNetworkServiceProvider.updateNetworkServiceProviderCmd()
        cmd.id = self.id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return apiclient.updateNetworkServiceProvider(cmd)

    @classmethod
    def update(cls, apiclient, id, **kwargs):
        """Updates network service provider"""

        cmd = updateNetworkServiceProvider.updateNetworkServiceProviderCmd()
        cmd.id = id
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return apiclient.updateNetworkServiceProvider(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List network service providers"""

        cmd = listNetworkServiceProviders.listNetworkServiceProvidersCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listNetworkServiceProviders(cmd))

class VpcOffering:
    """Manage VPC offerings"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services):
        """Create vpc offering"""

        cmd = createVPCOffering.createVPCOfferingCmd()
        cmd.name = "-".join([services["name"], random_gen()])
        cmd.displaytext = services["displaytext"]
        cmd.supportedServices = services["supportedservices"]
        return VpcOffering(apiclient.createVPCOffering(cmd).__dict__)

    def update(self, apiclient, name=None, displaytext=None, state=None):
        """Updates existing VPC offering"""

        cmd = updateVPCOffering.updateVPCOfferingCmd()
        cmd.id = self.id
        if name:
            cmd.name = name
        if displaytext:
            cmd.displaytext = displaytext
        if state:
            cmd.state = state
        return apiclient.updateVPCOffering(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List the VPC offerings based on criteria specified"""

        cmd = listVPCOfferings.listVPCOfferingsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listVPCOfferings(cmd))

    def delete(self, apiclient):
        """Deletes existing VPC offering"""

        cmd = deleteVPCOffering.deleteVPCOfferingCmd()
        cmd.id = self.id
        return apiclient.deleteVPCOffering(cmd)


class VPC:
    """Manage Virtual Private Connection"""

    def __init__(self, items):
        self.__dict__.update(items)

    @classmethod
    def create(cls, apiclient, services, vpcofferingid,
               zoneid, networkDomain=None, account=None, domainid=None):
        """Creates the virtual private connection (VPC)"""

        cmd = createVPC.createVPCCmd()
        cmd.name = "-".join([services["name"], random_gen()])
        cmd.displaytext = "-".join([services["displaytext"], random_gen()])
        cmd.vpcofferingid = vpcofferingid
        cmd.zoneid = zoneid
        cmd.cidr = services["cidr"]
        if account:
            cmd.account = account
        if domainid:
            cmd.domainid = domainid
        if networkDomain:
            cmd.networkDomain = networkDomain
        return VPC(apiclient.createVPC(cmd).__dict__)

    def update(self, apiclient, name=None, displaytext=None):
        """Updates VPC configurations"""

        cmd = updateVPC.updateVPCCmd()
        cmd.id = self.id
        if name:
            cmd.name = name
        if displaytext:
            cmd.displaytext = displaytext
        return (apiclient.updateVPC(cmd))

    def delete(self, apiclient):
        """Delete VPC network"""

        cmd = deleteVPC.deleteVPCCmd()
        cmd.id = self.id
        return apiclient.deleteVPC(cmd)

    def restart(self, apiclient):
        """Restarts the VPC connections"""

        cmd = restartVPC.restartVPCCmd()
        cmd.id = self.id
        return apiclient.restartVPC(cmd)

    @classmethod
    def list(cls, apiclient, **kwargs):
        """List VPCs"""

        cmd = listVPCs.listVPCsCmd()
        [setattr(cmd, k, v) for k, v in kwargs.items()]
        return(apiclient.listVPCs(cmd))

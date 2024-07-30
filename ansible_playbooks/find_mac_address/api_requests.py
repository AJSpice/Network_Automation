from http.cookiejar import MozillaCookieJar
import requests
import os
import sys
import getpass
import json
import yaml
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

cwd = os.getcwd()
username = input("Enter your username:\n")
password = getpass.getpass("Enter your password:\n")
mac_address = input("What MAC address are you looking for? In format of a1:b2:c3:d4:e5 \n")

mac_address = mac_address.lower()

def main():

    global username
    global password
    global mac_address
    
    with open (os.path.join(cwd , 'hosts.yml') , 'r') as f:
        hosts_data = yaml.safe_load(f)

        switches = hosts_data['MAIN']['hosts'].keys()

        for switch_ip in switches:
            
            cookie_file = os.path.join(cwd , 'cookies' , f'{switch_ip}_tmp_cookie_file')

            with open (os.path.join(cwd , 'logs' , f'{switch_ip}.logs') , 'w') as log_file:

                # Delete the cookie file if it exists
                if os.path.exists(cookie_file):
                    os.remove(cookie_file)

                # Create a new cookie file
                cookies = MozillaCookieJar(cookie_file)

                headers = {}

                files = {
                    'username': (None, username),
                    'password': (None, password),
                }

                # Use the same session for all requests
                with requests.Session() as session:

                    session.cookies = cookies

                    while True:
                        response = session.post(f'https://{switch_ip}/rest/v1/login', headers=headers, files=files, verify=False)

                        if response.status_code != 401:
                            break

                        print(f'LOGIN FAILED on {switch_ip} please try again or press Ctrl + C to break')
                        username = input("Enter your username:\n")
                        password = getpass.getpass("Enter your password:\n")
                        files = {
                            'username': (None, username),
                            'password': (None, password),
                            }

                    cookies.save(cookie_file, ignore_discard=True, ignore_expires=True)
                    log_file.write(f'The LOGIN status code is: {response.status_code}\n')

                    # find the vlans on the device
                    try:
                        response = session.get(f'https://{switch_ip}/rest/v10.10/system/vlans', headers=headers, verify=False)
                    except:
                        log_file.write(f"GET_VLAN FAILED on {switch_ip}")

                    log_file.write(f'\nThe GET_VLAN status code is: {response.status_code}\n')
                    vlan_response_text = response.text.strip()
                    log_file.write(f'The GET_VLAN output is: {vlan_response_text}\n')

                    response_json = json.loads(vlan_response_text)


                    for vlan,info in response_json.items():

                        final_check = {}

                        if int(vlan) != 1:
                            log_file.write(f"\nVLAN {vlan}\n")
                            mac_address_formatted = mac_address.replace(':' , '%3A')

                            headers = {
                                'accept': '*/*',
                                'Content-Type': 'application/json',
                            }

                            # look for mac addresses learned by port-access and log the findings
                            mac_port_access_response = session.get(f'https://{switch_ip}/rest/v10.04/system/vlans/{vlan}/macs/port-access-security,{mac_address_formatted}?attributes=mac_addr,port,denied', headers=headers, verify=False)
                            if mac_port_access_response.status_code == 404:
                                final_check[vlan] = "FAILED with error 404 on port access check"
                                log_file.write(f"MAC not found on {switch_ip} vlan {vlan}, Status code: {mac_port_access_response.status_code} PORT_ACCESS\n")
                            elif mac_port_access_response.status_code !=200:
                                final_check[vlan] = f"FAILED with error {mac_port_access_response.status_code}"
                                log_file.write(f"MAC_PORT_ACCESS FAILED on {switch_ip} vlan {vlan}, Status code: {mac_port_access_response.status_code}\n")

                            # look for mac addresses learned dynamically and log the findings
                            mac_dynamic_response = session.get(f'https://{switch_ip}/rest/v10.04/system/vlans/{vlan}/macs/dynamic,{mac_address_formatted}?attributes=mac_addr,port', headers=headers, verify=False)
                            if mac_dynamic_response.status_code == 404:
                                final_check[vlan] = "FAILED with error 404 on dynamic check"
                                log_file.write(f"MAC not found on {switch_ip} vlan {vlan}, Status code: {mac_dynamic_response.status_code} DYNAMIC\n")
                            elif mac_dynamic_response.status_code !=200:
                                final_check[vlan] = f"FAILED with error {mac_dynamic_response.status_code}"
                                log_file.write(f"MAC_DYNAMIC FAILED on {switch_ip} vlan {vlan}, Status code: {mac_dynamic_response.status_code}\n")

                            if mac_port_access_response.status_code == 200:
                                final_check[vlan] =  "SUCCESS with code 200 on port-access check"
                                found_mac = mac_port_access_response.text
                                print (f"\nFound MAC on switch {switch_ip} vlan {vlan}:\n{found_mac}")
                            elif mac_dynamic_response.status_code == 200:
                                final_check[vlan] = "SUCCESS with code 200 on dynamic check"
                                found_mac = mac_dynamic_response.text
                                print (f"\nFound MAC on switch {switch_ip} vlan {vlan}:\n{found_mac}")

                    print (final_check.values())
                            #if "SUCCESS" not in final_check.values():
                            #    print (f"MAC Address not found on network")
                            



                    # log out of this session
                    try:
                        response = session.post(f'https://{switch_ip}/rest/v10.04/logout', headers=headers, verify=False)
                    except:
                        log_file.write(f'LOGOUT FAILED on {switch_ip}')
                        
                    log_file.write(f'\nThe LOGOUT status code is: {response.status_code}\n')



if __name__ == "__main__":
    main()



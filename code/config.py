from pathlib import Path
import tomlkit
import os
import re
import requests
from enum import Enum
from tempfile import TemporaryDirectory

#Thanks to Jeet, for his anwser https://stackoverflow.com/questions/2514859/regular-expression-for-git-repository
GIT_URL = re.compile(r"((\w+://)(.+@)*([\w\d\.]+)(:[\d]+){0,1}/*(.*))|(file://(.*))|((.+@)*([\w\d\.]+):(.*))")

#Thanks to cetver for showing how django soleves validating urls. https://stackoverflow.com/questions/7160737/python-how-to-validate-a-url-in-python-malformed-or-not/36283503
URL = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)




class ConfigError(Exception):
    def __init__(self,message:str):
        super().__init__(message)




class Config:

    def __init__(self,path=Path(__file__).parent / "../config.toml"):
        #Wrapper calss for config.toml file
        with open(path) as fp:
            self.conf = tomlkit.parse(fp.read())



        if not self.conf["Servers"].get("implementations",False):
            if self.conf["Servers"].get("implementation",False):
                raise ConfigError("The config must have a entry [Servers.implementations] not [Servers.implementation] (it's missing a s)")
            else:
                raise ConfigError("The config must have a entry [Servers.implementations]")

        implementations = set(x for x in self.conf["Servers"]["implementations"])


        for server in self.conf["Servers"]:

            if server in ["implementations"]:
                continue

            if self.conf["Servers"][server].get("implementations"):
                 raise ConfigError(f"The entry [Servers.{server}] 'implementations' field is not valid, because its should be 'implementation' and not 'implementations'.")
            if self.conf["Servers"][server].get("implementation") not in implementations:
                raise ConfigError(f"The entry [Servers.{server}] 'implementation' field {self.conf['Servers'][server].get('implementaion')} is not a server implementation refferenced in the implementations field: {implementations}.")
                
            if directory := self.conf["Servers"][server].get("directory",""):
                if not os.path.isabs(directory):
                    #Change all paths to be absolute, and not relative to were the program is started from. 
                    self.conf["Servers"][server]["directory"] = str((Path(__file__).parent.parent /  self.conf["Servers"][server]["directory"]).absolute())
                if not os.path.exists(self.conf["Servers"][server]["directory"]) and not os.path.isdir(self.conf["Servers"][server]["directory"]):
                    raise ConfigError(f"The entry [Servers.{server}] directory field {self.conf['Servers'][server]['directory']} is not a valid directory.")
                
                # If a server entry has a directory entry, we then dont want it to also have a git url/branch.
                if self.conf["Servers"][server].get("git_url",None):
                    raise ConfigError(f"The entry [Servers.{server}] has a directory entry and a git_url entry. It can only have one of them.")
                
                if self.conf["Servers"][server].get("git_branch",None):
                    raise ConfigError(f"The entry [Servers.{server}] has a directory entry and a git_branch entry. It can only have one of them.")
                
                if self.conf["Servers"][server].get("download_url",None):
                    raise ConfigError(f"The entry [Servers.{server}] has a download_url entry and a git_url entry. It can only have one of them.")
                
            elif git_url := self.conf["Servers"][server].get("git_url",""):
                #Check that url exists and is valid
                if not GIT_URL.match(git_url):
                    raise ConfigError(f"The git_url for the Entry [Server.{server}] does not look like a valid git url.")
                
                if git_url.startswith("http") or git_url.startswith("https"):
                    #Then we request excluding the .git, giving a reponse that determines the existance of repocitory
                    response = requests.get(git_url.strip(".git"))
                    if not (200 <= response.status_code <= 299):
                        raise ConfigError(f"The entry [Servers.{server}] git url gives bad response code: {response.status_code}")
                    
                #We cant have git_url and a download_url
                if self.conf["Servers"][server].get("download_url",None):
                    raise ConfigError(f"The entry [Servers.{server}] has 'download_url' and 'git_url'. It can only have one of them.")
                    
                    
            elif download_url := self.conf["Servers"][server].get("download_url"):

                if not re.match(URL,download_url):
                    ConfigError(f"The entry [Servers.{server}] has the download_url:{download_url}, that was not detected as valid.")


            else:
                raise ConfigError(f"The entry [Servers.{server}] must have one of 'git_url' and 'directory' fields.")


        for server in self.conf.get("Server",[]):
            raise ConfigError(f"The entry [Server.{server}] is a misspelling, it should be plural [Servers.{server}]!")
    
    

        #Create a enum that we use to refference to a specific server, the name and value of these enums are the same.
        self.server_names = Enum("ServerNames",[(x,x) for x in self.conf["Servers"]])
        self.server_names.__str__ = lambda self: self.name
        



        
if __name__ == "__main__":
    Config()
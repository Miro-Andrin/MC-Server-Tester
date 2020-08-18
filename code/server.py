import enum, os
from tempfile import TemporaryDirectory
import pathlib
import tempfile
from pathlib import Path
import shutil

from config import Config
import subprocess
import sys
import shlex
import requests
import time


class Server():

    def __init__(self,config:Config,server):

        if not type(server) == type(config.server_names) and server not in map(str,config.server_names) :
            print(f"The server {server} is not defined in the config")


        #The version is a string lik "Feather_1_13_2" or "Spigot_1_13_2
        #in the config.toml file these are the names of all the servers defined. 

        self.conf = config.conf["Servers"][str(server)]
        self.server_name = str(server)

    def __enter__(self):
        """
        Creates a temp directory, and moves all the server files into the temp folder.
        If the config has specified that the server is a git based one, then we clone into
        that folder. 
        """
        temp_dir = tempfile.TemporaryDirectory()

        print(f"Creating a server instance in {temp_dir.name} for {self.server_name}")

        if directory := self.conf.get("directory",False):
            shutil.copytree(Path(directory),Path(temp_dir.name),dirs_exist_ok=True)
        
        elif git_url := self.conf.get("git_url",False):

            if git_branch := self.conf.get("git_branch"):
                clone_process = subprocess.run(["git", "clone","-b",git_branch ,git_url, temp_dir])
                if returncode := clone_process.returncode != 0:
                    print(f"The cloning of {git_url} into {temp_dir.name} failed")
                    sys.exit(returncode)
            else:
                clone_process = subprocess.run(["git", "clone" ,git_url, temp_dir])
                if returncode := clone_process.returncode != 0:
                    print(f"The cloning of {git_url} into {temp_dir.name} failed")
                    sys.exit(returncode)
        
        elif download_url := self.conf.get("download_url",False):
            print(f"Downloading server from {download_url}:")
            filename = str(download_url.split("/")[-1])
            #Download should probably be cahed. 
            with open((Path(temp_dir.name) / filename), "wb") as fp:
                r = requests.get(download_url, allow_redirects=True)
                assert r.ok #TODO report errors
                fp.write(r.content)

            #When downloading cuberite we get a tar.gz (linux/macOS) or a zip (windows) 
            if filename.endswith(".tar.gz"):
                print("Unpacking tar.gz file")
                tar_prosess = subprocess.run(["tar","-C",str(Path(temp_dir.name)),"-xvf",str(Path(temp_dir.name) / filename)], stdout=subprocess.DEVNULL)
                if returncode := tar_prosess.returncode != 0:
                    print(f"The un-taring of {str(Path(temp_dir.name) / filename)} into {temp_dir.name} failed")
                    sys.exit(tar_prosess)
            

            
        else:
            assert False


        if build_command := self.conf.get("build_command",False):
            build_process = subprocess.run(shlex.split(build_command))
            if returncode := build_process.returncode != 0:
                print(f"The building of {self.server_name} in {temp_dir.name} failed!")
                sys.exit(returncode)


        self._instance = ServerInstace(self.conf,self.server_name,temp_dir)       
        return self._instance

    def __exit__(self,_type,server,traceback):
        self._instance.terminate()
        self._instance.directory.cleanup()

    

class ServerInstace:
    
    def __init__(self,config:Config,server_name:str,directory:TemporaryDirectory):

        self.directory = directory
        self.name = server_name
        self.conf = config



        self.prosess = None

    def start(self):
        #Starts server instance with all the settings that you have specified.

        #@TODO write all changed variables to config files.

        if self.prosess != None:
            assert False #
        
        #@TODO maybe write output to some sort of log?
        self.prosess = subprocess.Popen(shlex.split(self.conf["start_command"]), cwd=self.directory.name)
        

        return 

    def onlineMode(self):
        ...

    def terminate(self):
        # Kills the server if its running
        if self.prosess == None:
            return
        else:
            self.prosess.terminate()






    
    




if __name__ == "__main__":
    c = Config()

    with Server(c,"Feather_1_13_2") as server:
        server.onlineMode = False
        server.maxPlayers = 100
        server.gamemode = 1 #creative
        server.start()
        time.sleep(10)


    with Server(c,"Vanilla_1_13_2") as server:
        server.onlineMode = False
        server.maxPlayers = 100
        server.gamemode = 1 #creative
        server.start()
        time.sleep(10)


    with Server(c,"Cuberite_1_12_2") as server:
        server.onlineMode = False
        server.maxPlayers = 100
        server.gamemode = 1 #creative
        server.start()
        time.sleep(10)
        


    
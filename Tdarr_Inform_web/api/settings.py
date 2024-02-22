from flask import request, redirect, Response, session
import urllib.parse
import threading
import time
import json
from io import StringIO


class Settings():
    endpoints = ["/api/settings"]
    endpoint_name = "api_settings"
    endpoint_methods = ["GET", "POST"]

    def __init__(self, tdarr_inform):
        self.tdarr_inform = tdarr_inform

        self.restart_url = "/api/settings?method=restart_actual"
        self.restart_sleep = 5

    def __call__(self, *args):
        return self.handler(*args)

    def handler(self, *args):

        method = request.args.get('method', default="get", type=str)
        redirect_url = request.args.get('redirect', default=None, type=str)

        if method == "get":
            web_settings_dict = {}
            for config_section in list(self.tdarr_inform.config.conf_default.keys()):
                web_settings_dict[config_section] = {}

                for config_item in list(self.tdarr_inform.config.conf_default[config_section].keys()):
                    web_settings_dict[config_section][config_item] = {
                        "value": self.tdarr_inform.config.dict[config_section][config_item],
                        }
                    if self.tdarr_inform.config.conf_default[config_section][config_item]["config_web_hidden"]:
                        web_settings_dict[config_section][config_item]["value"] = "***********"

            return_json = json.dumps(web_settings_dict, indent=4)

            return Response(status=200,
                            response=return_json,
                            mimetype='application/json')

        elif method == "ini":
            fakefile = StringIO()

            web_settings_dict = {}
            for config_section in list(self.tdarr_inform.config.conf_default.keys()):
                fakefile.write("[%s]\n" % config_section)

                for config_item in list(self.tdarr_inform.config.conf_default[config_section].keys()):
                    value = self.tdarr_inform.config.dict[config_section][config_item]
                    if self.tdarr_inform.config.conf_default[config_section][config_item]["config_web_hidden"]:
                        value = "***********"
                    fakefile.write("%s = %s\n" % (config_item, value))

            config_ini = fakefile.getvalue()

            resp = Response(status=200, response=config_ini, mimetype='text/html')
            resp.headers["content-disposition"] = "attachment; filename=config.ini"
            return resp

        elif method == "update":
            config_section = request.form.get('config_section', None)
            config_name = request.form.get('config_name', None)
            config_value = request.form.get('config_value', None)

            if not config_section or not config_name:
                if redirect_url:
                    return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Failed" % method)))
                else:
                    return "%s Falied" % method

            self.tdarr_inform.config.write(config_name, config_value, config_section)

        elif method == "restart":
            restart_thread = threading.Thread(target=self.restart_thread)
            restart_thread.start()
            return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("Restarting in %s seconds" % self.restart_sleep)))

        elif method == "restart_actual":
            session["restart"] = True

        if redirect_url:
            if "?" in redirect_url:
                return redirect("%s&retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
            else:
                return redirect("%s?retmessage=%s" % (redirect_url, urllib.parse.quote("%s Success" % method)))
        else:
            return "%s Success" % method

    def restart_thread(self):
        time.sleep(self.restart_sleep)
        try:
            self.tdarr_inform.api.get(self.restart_url)
        except AttributeError:
            return

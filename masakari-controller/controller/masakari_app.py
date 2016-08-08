#
# Copyright (c) 2016, Platform9 Systems. All Rights Reserved
#

from masakari_controller import RecoveryController


class MasakariApp(object):
    def __init__(self):
        self._rc = RecoveryController()
        self._rc.masakari()

    def __call__(self, environ, start_response):
        return self._rc.call(environ, start_response)


def app_factory(global_config):
    return MasakariApp()


def main():
    from paste import httpserver
    from paste.deploy import loadapp
    httpserver.serve(loadapp('config:masakari-api-paste.ini', relative_to='/etc/masakari'),
                     host='127.0.0.1', port='15868')

if __name__ == "__main__":
    main()
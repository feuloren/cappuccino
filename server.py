# -*- coding:utf-8 -*-

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from waitress import serve
import json
import settings
from printer import print_billet, ouvrir_caisse, is_printer_present
from pcsc import pcsc

class CrossSiteResponse(Response):
    """Le serveur va tourner sur le PC caisse du Polar.
    Pour des raisons de sécurité firefox n'autorise pas la lecture de la réponse d'une requête ajax faites sur un autre domaine.
    On va préciser les en-têtes Origin et Access-Control-Allow-Origin pour autoriser la caisse à les lire.
    cf https://developer.mozilla.org/en-US/docs/HTTP/Access_control_CORS
    """
    def __init__(self, body, *args, **kwargs):
        kwargs['body'] = json.dumps(body)
        super(CrossSiteResponse, self).__init__(*args, **kwargs)
        self.headers['Origin'] = settings.domain
        self.headers['Access-Control-Allow-Origin'] = '*'
        self.content_type = 'application/json'

def do_print_billet(request):
    numero = int(request.POST.get('id'))
    nom = request.POST.get('nom')
    type = request.POST.get('type')
    code = request.POST.get('code')
    print_billet(numero, nom, type, code)

    return CrossSiteResponse(True)

def do_caisse(request):
    ouvrir_caisse()
    return CrossSiteResponse(True)

def do_smartcard(request):
    card = pcsc.wait_for_smartcard()
    return CrossSiteResponse(card)

def do_reset(request):
    pcsc.reset()
    return CrossSiteResponse(True)

def do_capabilities(request):
    """Est-ce que l'imprimante est connectée ? Et le lecteur de carte étu ?"""
    result = {'printer':is_printer_present(),
              'smartcard':pcsc.is_reader_present()}
    return CrossSiteResponse(result)

def run():
    config = Configurator()

    config.add_route('reset', '/reset')
    config.add_view(do_reset, route_name='reset')

    config.add_route('caisse', '/caisse')
    config.add_view(do_caisse, route_name='caisse')

    config.add_route('capabilities', '/capabilities')
    config.add_view(do_capabilities, route_name='capabilities')

    config.add_route('print_billet', '/billet')
    config.add_view(do_print_billet, route_name='print_billet')

    config.add_route('smartcard', '/smartcard')
    config.add_view(do_smartcard, route_name='smartcard')

    app = config.make_wsgi_app()
    serve(app, host='127.0.0.1', port=8000)

if __name__ == '__main__':
    run()

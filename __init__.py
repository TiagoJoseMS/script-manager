# -*- coding: utf-8 -*-
"""
Script Manager Plugin
Inicializador do plugin para QGIS
"""

def classFactory(iface):
    """
    Função obrigatória que retorna a instância da classe do plugin
    """
    from .script_manager import ScriptManager
    return ScriptManager(iface)

const yaml = require('js-yaml');
const fs = require('fs');
const express = require('express');
const respuesta = require('../../red/respuestas');
const controlador = require("./controlador");

const router = express.Router();

router.get('/getYAML',getYAML );
router.get('/getAllOIDs',getAllOIDs );
router.post('/editYAML',editYAML );


// let archivo = '/usr/smartlink/general/snmp/perfil_extraccion_oid.yml';
let archivo = '/usr/smartlink/general/snmp/configuration_snmp.yml';
// let archivo = '/usr/smartlink/general/snmp/test_snmp.yml';
// let archivo = '/usr/smartlink/general/snmp/snmp_available.yml';

async function getYAML(req, res, next) {
    try {
        const fileContents = fs.readFileSync(archivo, 'utf8');
        respuesta.success(req, res, yaml.load(fileContents), 200);
    } catch (e) {
        next(e)
    }
}

async function getAllOIDs(req, res, next) {
    try {
        await controlador.getAllOIDs(res);
    } catch (error) {
        next(error);
    }
}

async function editYAML(req, res, next) {
    let datos = req.body.yaml;
    
    try {
        const yamlString = yaml.dump(datos);
        fs.writeFileSync(archivo, yamlString, 'utf8');
        respuesta.success(req, res, 'Archivo Modificado', 200);
    } catch (e) {
      respuesta.error(req, res, e, 200);
    }
}

module.exports = router;

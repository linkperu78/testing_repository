const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getDataBaseStatus", getDataBaseStatus);

async function getDataBaseStatus(req, res, next) {
  try {
    await controlador.getDataBaseStatus(res);
  } catch (error) {
    next(error);
  }
}

module.exports = router;

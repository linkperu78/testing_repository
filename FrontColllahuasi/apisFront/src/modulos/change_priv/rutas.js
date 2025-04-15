const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/", getPageStatus);

async function getPageStatus(req, res, next) {
  try {
    await controlador.getPageStatus(res);
  } catch (error) {
    next(error);
  }
}

module.exports = router;

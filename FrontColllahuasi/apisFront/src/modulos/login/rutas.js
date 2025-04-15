const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/", getUserLogin);

//get All data from LTE Table
async function getUserLogin(req, res, next) {
  try {
    const items = await controlador.getUserLogin(
      req.query.user,
      req.query.pass
    );
    respuesta.success(req, res, items, 200);
  } catch (error) {
    next(error);
  }
}

module.exports = router;

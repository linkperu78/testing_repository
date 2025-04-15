const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getClustering", getClustering);
router.get("/getClusteringData", getClusteringData);
router.get("/getLast12HourClustering", getLast12HourClustering);

//Call in DASHBOARDVIEW
//Call in COSTMAPSQLVIEW
async function getClustering(req, res, next) {
  try {
    await controlador.getClustering(res);
  } catch (error) {
    next(error);
  }
}

async function getClusteringData(req, res, next) {
  try {
    await controlador.getClusteringData(res, req.query.fecha);
  } catch (error) {
    next(error);
  }
}

async function getLast12HourClustering(req, res, next) {
  try {
    await controlador.getLast12HourClustering(res);
  } catch (error) {
    next(error);
  }
}

module.exports = router;

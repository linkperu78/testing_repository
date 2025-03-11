const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/", allData);
router.post("/", addData);
router.put("/", editData);
router.delete("/deleteData", deleteData);
router.get("/getSubTypeInventory", getSubTypeInventory);
router.get("/getTypeInventory", getTypeInventory);
router.get("/getMarkInventory", getMarkInventory);
router.get("/getSNMPInventory", getSNMPInventory);
router.delete("/deleteDataInDB", deleteDataInDB);

//get All data from Inventory Table
async function allData(req, res, next) {
  try {
    const items = await controlador.getAllData();
    respuesta.success(req, res, items, 200);
  } catch (error) {
    // respuesta.error(req, res, err, 500);
    next(error);
  }
}

//Add Info in Inventory table
async function addData(req, res, next) {
  try {
    await controlador.addData(req.body);
    respuesta.success(req, res, "Item agregado!", 200);
  } catch (error) {
    // respuesta.error(req, res, err, 500);
    next(error);
  }
}

//Update Info in Inventory table
async function editData(req, res, next) {
  try {
    const items = await controlador.editData(req.body);
    respuesta.success(req, res, "Item Modificado", 200);
  } catch (error) {
    // respuesta.error(req, res, err, 500);
    next(error);
  }
}

//Delete Info in Inventory table
async function deleteData(req, res, next) {
  let table   = req.query.table;
  let ip      = req.query.ip;
  let id      = req.query.id;
  try {
    const items = await controlador.deleteData(table, ip, id);
    respuesta.success(req, res, table + ' Eliminado', 200);
  } catch (error) {
    next(error);
  }
}

async function getSubTypeInventory(req, res, next) {
  console.log(req.params.id);
  try {
    await controlador.getSubTypeInventory(res);
  } catch (error) {
    next(error);
  }
}

async function getTypeInventory(req, res, next) {
  try {
    await controlador.getTypeInventory(res);
  } catch (error) {
    next(error);
  }
}

async function getMarkInventory(req, res, next) {
  try {
    await controlador.getMarkInventory(res);
  } catch (error) {
    next(error);
  }
}

async function getSNMPInventory(req, res, next) {
  try {
    await controlador.getSNMPInventory(res);
  } catch (error) {
    next(error);
  }
}

async function deleteDataInDB(req, res, next) {
  let table = req.query.table;
  let time = req.query.time;
  try {
    const items = await controlador.deleteDataInDB(table, time);
    respuesta.success(req, res, table, 200);
  } catch (error) {
    respuesta.error(req, res, err, 500);
  }
}

module.exports = router;

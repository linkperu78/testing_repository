const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getDataInventory", getDataInventory);
router.put("/editDataInventory", editDataInventory);
router.put("/editDataInventoryByName", editDataInventoryByName);
router.post("/insertDataInventory", insertDataInventory);


// Call in ADMINCSVVIEW
async function editDataInventory(req, res, next) {
  try {
    await controlador.editDataInventory(req.body);
    respuesta.success(req, res, "Item Modificado", 200);
  } catch (error) {
    next(error);
  }
}

// Call in ADMINCSVVIEW
async function editDataInventoryByName(req, res, next) {
  try {
    await controlador.editDataInventoryByName(req.body);
    respuesta.success(req, res, "Item Modificado", 200);
  } catch (error) {
    next(error);
  }
}

// Call in ADMINCSVVIEW
async function insertDataInventory(req, res, next) {
  try {
    await controlador.insertDataInventory(req.body);
    respuesta.success(req, res, "Item Insertado", 200);
  } catch (error) {
    next(error);
  }
}


// Call in ADMINCSVVIEW
async function getDataInventory(req, res, next) {
  try {
    const items = await controlador.getDataInventory(res);
  } catch (error) {
    next(error);
  }
}


module.exports = router;

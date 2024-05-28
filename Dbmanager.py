from pymongo import MongoClient

class MongoDBManager:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client['local']
        print("Conexión a MongoDB establecida.")
    
    def crear_coleccion_ventas(self, ano):
        coleccion_nombre = f'ventas-{ano}'
        self.ventas = self.db[coleccion_nombre]
        print(f"Colección '{coleccion_nombre}' preparada.")
        
        documento_inicial = {
            "nombre": "documento_inicial",
            "descripcion": f"Este es un documento inicial para asegurar la creación de la colección '{coleccion_nombre}'."
        }
        self.ventas.insert_one(documento_inicial)
        print(f"Documento inicial insertado en la colección '{coleccion_nombre}'.")

    def insertar_venta(self, ano, mes, unidadesVendidas, ganancias):
        coleccion_nombre = f'ventas-{ano}'
        self.ventas = self.db[coleccion_nombre]
        
        if self.ventas.count_documents({}) == 0:
            self.crear_coleccion_ventas(ano)
        
        existing_document = self.ventas.find_one({"mes": mes})
        
        if existing_document:
            self.ventas.update_one(
                {"mes": mes},
                {"$inc": {"unidadesVendidas": unidadesVendidas, "ganancias": ganancias}}
            )
            print(f"Documento existente actualizado en el mes {mes} del año {ano} con incremento de unidadesVendidas: {unidadesVendidas} y ganancias: {ganancias}")
        else:
            documento = {
                "mes": mes,
                "unidadesVendidas": unidadesVendidas,
                "ganancias": ganancias,
                "anioVenta": ano
            }
            self.ventas.insert_one(documento)
            print(f"Nuevo documento insertado en el mes {mes} del año {ano} con unidadesVendidas: {unidadesVendidas} y ganancias: {ganancias}")

    def recuperar_ventas_globales(self):
        colecciones = self.db.list_collection_names(filter={"name": {"$regex": "^ventas-"}})
        todas_las_ventas = []
        
        for coleccion_nombre in colecciones:
            coleccion = self.db[coleccion_nombre]
            documentos = list(coleccion.find({"unidadesVendidas": {"$exists": True}, "ganancias": {"$exists": True}, "anioVenta": {"$exists": True}, "mes": {"$exists": True}}, {"_id": 0, "mes": 1, "unidadesVendidas": 1, "ganancias": 1, "anioVenta": 1}))
            todas_las_ventas.extend(documentos)
        
        print(f"Documentos globales recuperados: {todas_las_ventas}")
        return todas_las_ventas

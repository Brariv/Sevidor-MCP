MARCAS = {
    "get_faq_maxicrez": "maxicrez",
    "get_faq_diabelife": "diabelife",
    "get_faq_colonditox": "colonditox",
    "get_faq_geriaking_vital": "geriaking vital",
    "get_faq_perenterol": "perenterol",
    "get_faq_calmiderm": "calmiderm",
}

TOOLS = [
    {
        "name": tool_name,
        "description": (
                    f"Consulta las preguntas frecuentes del producto. {marca.title()}"
                    "Formula el argumento 'pregunta' como una pregunta completa y explícita, "
                    "expandiendo referencias vagas. Por ejemplo, si el usuario dice "
                    "'¿cuánto cuesta?', envía '¿Cuál es el precio del producto?'."
                ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pregunta": {
                    "type": "string",
                    "description": "Pregunta del usuario sobre el producto",
                }
            },
            "required": ["pregunta"],
        },
    }
    for tool_name, marca in MARCAS.items()
] + [
    {
        "name": "consultar_faq_producto",
        "description": (
            "Devuelve la lista completa de preguntas frecuentes disponibles para un "
            "producto de la farmacia. Úsala para conocer qué preguntas existen antes "
            "de consultar una respuesta específica con get_faq_<producto>."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "marca": {
                    "type": "string",
                    "enum": sorted(set(MARCAS.values())),
                    "description": "Nombre del producto a consultar",
                }
            },
            "required": ["marca"],
        },
    },
] + [
    {
        "name": tool_name+"_exacta",
        "description": 
            "Busca la pregunta exacta en la FAQ, "
            "usa este metodo si ya sabes como esta la pregunta en la FAQ, "
            "para obtener la respuesta exacta.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pregunta": {
                    "type": "string",
                    "description": "Pregunta del usuario sobre el producto",
                }
            },
            "required": ["pregunta"],
        },
    }for tool_name, marca in MARCAS.items()
]


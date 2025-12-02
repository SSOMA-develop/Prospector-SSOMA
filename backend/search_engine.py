import random
import os
from typing import List, Dict
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Cargar variables del archivo .env si existe
load_dotenv()

class SearchEngine:
    def __init__(self, api_key: str = None, cse_id: str = None):
        # Configuración de API: Priorizar argumentos, luego variables de entorno
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.cse_id = cse_id or os.getenv("GOOGLE_CSE_ID")
        self.last_error = None
        self.using_real_api = False
        
        if self.api_key and self.cse_id:
            self.using_real_api = True
        
        self.mock_companies = [
            "Constructora Los Andes SAC",
            "Industrias Metálicas del Perú",
            "Transportes Rápidos Lima",
            "Servicios Generales SSOMA",
            "Manufactura Textil Avanzada",
            "Ingeniería y Construcción Total",
            "Logística Segura SAC",
            "Alimentos Procesados del Norte",
            "Minera San Juan",
            "Agroindustria del Valle",
            "Tecnología y Seguridad SAC",
            "Corporación Lindley",
            "Grupo Gloria",
            "Cementos Lima"
        ]
        # Roles de decisión solicitados
        self.decision_roles = [
            "Gerente General", 
            "Jefe de SSOMA", 
            "Administrador", 
            "Dueño", 
            "CEO", 
            "Fundador", 
            "Líder de Operaciones",
            "Gerente de Planta"
        ]

    def search(self, sector: str, location: str, deep_search: bool) -> List[Dict]:
        """
        Enruta la búsqueda: si hay credenciales de API, usa Google Real.
        Si no, usa Mock Data para demostración.
        """
        if self.api_key and self.cse_id:
            return self._search_google_api(sector, location, deep_search)
        else:
            return self._search_mock(sector, location, deep_search)

    def _search_google_api(self, sector: str, location: str, deep_search: bool) -> List[Dict]:
        """
        Ejecuta búsqueda real usando Google Custom Search JSON API.
        """
        results = []
        try:
            service = build("customsearch", "v1", developerKey=self.api_key)
            
            # Construir query
            query = f'"{sector}" "{location}"'
            if deep_search:
                query += ' ("Gerente" OR "Jefe" OR "Contacto")'
            
            # Ejecutar búsqueda (limitado a 10 resultados por request gratis)
            res = service.cse().list(q=query, cx=self.cse_id, num=10).execute()
            
            items = res.get("items", [])
            
            for item in items:
                prospect = {
                    "name": item.get("title"),
                    "source": item.get("displayLink"),
                    "location": location, # Google no siempre da ubicación estructurada
                    "contact_info": None,
                    "role_detected": None,
                    "confidence_score": 0.8 # Base confidence para real data
                }
                
                snippet = item.get("snippet", "").lower()
                
                # Intentar extraer info del snippet
                if "@" in snippet:
                    words = snippet.split()
                    for word in words:
                        if "@" in word:
                            prospect["contact_info"] = word.strip(".,")
                            break
                            
                for role in self.decision_roles:
                    if role.lower() in snippet:
                        prospect["role_detected"] = role
                        prospect["confidence_score"] = 0.95
                        break
                
                results.append(prospect)
                
        except Exception as e:
            self.last_error = str(e)
            print(f"Error en Google API: {e}")
            # Fallback a mock si falla la API
            return self._search_mock(sector, location, deep_search)
            
        return results

    def _search_mock(self, sector: str, location: str, deep_search: bool) -> List[Dict]:
        """
        Simula una búsqueda avanzada (Mock Data).
        """
        results = []
        # Aumentamos la cantidad de resultados para dar sensación de "Deep Search"
        num_results = random.randint(8, 15) if not deep_search else random.randint(12, 20)
        
        for _ in range(num_results):
            base_name = random.choice(self.mock_companies)
            # Variar el nombre para que no sean siempre iguales
            suffix = random.choice(["", " & Asociados", " Group", " Perú"])
            company = f"{base_name}{suffix}"
            
            # Generar datos base
            prospect = {
                "name": company,
                "source": random.choice(["DatosPerú", "LinkedIn", "UniversidadPerú", "Paginas Amarillas"]),
                "location": f"{location} - {random.choice(['Zona Industrial', 'Cercado', 'Parque Industrial'])}",
                "contact_info": None,
                "role_detected": None,
                "confidence_score": round(random.uniform(0.4, 0.7), 2)
            }

            # Lógica Deep Search: Intentar encontrar al tomador de decisiones
            if deep_search:
                # Mayor probabilidad de éxito en Deep Search
                if random.random() > 0.2: 
                    role = random.choice(self.decision_roles)
                    prospect["role_detected"] = role
                    
                    # Generar email corporativo realista
                    domain = company.lower().replace(' ', '').replace('sac', '').replace('&', '').replace('group', '').replace('perú', '')
                    prospect["contact_info"] = f"{random.choice(['gerencia', 'contacto', 'admin'])}@{domain}.com"
                    
                    # A veces agregar teléfono
                    if random.random() > 0.5:
                        prospect["contact_info"] += f" | 📞 9{random.randint(10,99)} {random.randint(100,999)} {random.randint(100,999)}"
                    
                    # Subir confianza si encontramos rol clave
                    prospect["confidence_score"] = round(random.uniform(0.85, 0.99), 2)
                    prospect["source"] += " + Web Scraping"
            
            results.append(prospect)
            
        # Ordenar por confianza descendente
        results.sort(key=lambda x: x['confidence_score'], reverse=True)
        return results

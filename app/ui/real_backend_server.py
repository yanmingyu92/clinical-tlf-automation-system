#!/usr/bin/env python3
"""
Production Backend Server for Clinical TLF UI
=============================================

Clean implementation supporting the 4-step production workflow:
- Step 1: Query analysis (/analyze)
- Step 2: Template generation (/generate_quality_template)  
- Step 3: R code generation (/generate_quality_rcode)
- Step 4: R code execution (/execute_rcode)

Author: Jaime Yan
Date: August 26, 2025
"""

import http.server
import socketserver
import json
import os
import sys
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionBackendHandler(http.server.SimpleHTTPRequestHandler):
    """Clean production handler for 4-step clinical TLF workflow"""
    
    def __init__(self, *args, **kwargs):
        # Initialize AI components once (class-level singleton)
        if not hasattr(self.__class__, '_components'):
            logger.info("🚀 Initializing production AI components...")
            self.__class__._components = self._initialize_components()
        super().__init__(*args, **kwargs)

    def setup(self):
        """Setup connection with timeout to prevent hanging"""
        super().setup()
        # Set socket timeout to prevent hanging connections
        if hasattr(self, 'request') and hasattr(self.request, 'settimeout'):
            self.request.settimeout(300)  # 5 minutes timeout
            logger.debug(f"🔧 Connection timeout set to 300 seconds")

    @property
    def components(self):
        """Access class-level AI components"""
        return self.__class__._components

    def _initialize_components(self) -> Dict[str, Any]:
        """Initialize production AI components"""
        components = {}
        
        try:
            # Add project paths
            current_dir = os.path.dirname(__file__)
            app_dir = os.path.dirname(current_dir)
            project_dir = os.path.dirname(app_dir)
            
            for path in [app_dir, project_dir]:
                if path not in sys.path:
                    sys.path.insert(0, path)

            # Initialize Unified LLM Client (user-selectable provider)
            from app.api.unified_llm_client import UnifiedLLMClient
            components['llm_client'] = UnifiedLLMClient(preferred_provider="deepseek")
            available_providers = components['llm_client'].get_available_providers()
            logger.info(f"✅ Unified LLM Client initialized")
            logger.info(f"📋 Available providers: {', '.join(available_providers)}")
            logger.info(f"🎯 Current provider: {components['llm_client'].get_current_provider()}")

            # Initialize RAG System
            try:
                from rag.template_rag import template_rag
                components['rag_system'] = template_rag
                logger.info("✅ RAG system initialized")
            except Exception as e:
                logger.warning(f"⚠️ RAG system unavailable: {e}")
                components['rag_system'] = None

            components['status'] = 'ready'
            
        except Exception as e:
            logger.error(f"❌ Component initialization error: {e}")
            components['status'] = f'error: {str(e)}'
            
        return components

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/index.html':
            self.serve_html_file('real_ui.html')
        elif self.path == '/status':
            self.handle_status()
        elif self.path.startswith('/get_file_content'):
            self.handle_get_file_content()
        elif self.path.startswith('/components/'):
            self.serve_component_file()
        elif self.path.startswith('/css/') or self.path.startswith('/js/') or self.path.startswith('/assets/'):
            self.serve_static_file()
        else:
            super().do_GET()

    def do_POST(self):
        """Handle POST requests for 4-step workflow"""
        try:
            # Parse request
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}

            # Route to appropriate handler
            if self.path == '/analyze':
                self.handle_step1_analyze(data)
            elif self.path == '/generate_quality_template':
                self.handle_step2_template(data)
            elif self.path == '/generate_quality_rcode':
                self.handle_step3_rcode(data)
            elif self.path == '/execute_rcode':
                self.handle_step4_execute(data)
            elif self.path == '/api/step4/interactive/initialize':
                self.handle_step4_interactive_initialize(data)
            elif self.path == '/api/step4/interactive/chat':
                logger.info(f"🔍 BACKEND: *** INTERACTIVE CHAT REQUEST RECEIVED ***")
                logger.info(f"🔍 BACKEND: Request data keys: {list(data.keys())}")
                if 'context' in data and 'execution_id' in data['context']:
                    logger.info(f"🔍 BACKEND: Execution ID: {data['context']['execution_id']}")
                self.handle_step4_interactive_chat(data)
            elif self.path == '/api/step4/interactive/interrupt':
                self.handle_step4_interactive_interrupt(data)
            elif self.path == '/api/step4/interactive/restart':
                self.handle_step4_interactive_restart(data)
            elif self.path == '/explore_dataset':
                self.handle_explore_dataset(data)
            elif self.path == '/validate_rcode':
                self.handle_validate_rcode(data)
            elif self.path == '/debug_code':
                self.handle_debug_code(data)
            elif self.path == '/debug_chat':
                self.handle_debug_chat(data)
            elif self.path == '/explain_r_code':
                self.handle_explain_rcode(data)
            elif self.path == '/set_llm_provider':
                self.handle_set_llm_provider(data)
            elif self.path == '/get_llm_providers':
                self.handle_get_llm_providers(data)
            elif self.path == '/api/llm/providers':
                self.handle_get_llm_providers(data)
            elif self.path == '/api/llm/change_provider':
                self.handle_set_llm_provider(data)
            else:
                self.send_error(404, f"Unknown endpoint: {self.path}")
                
        except Exception as e:
            logger.error(f"POST error: {e}")
            self.send_error(500, str(e))

    def serve_html_file(self, filename):
        """Serve the UI HTML file"""
        try:
            file_path = os.path.join(os.path.dirname(__file__), filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error serving {filename}: {e}")
            self.send_error(404, f"File not found: {filename}")

    def serve_component_file(self):
        """Serve component files"""
        try:
            # Remove leading slash and get relative path
            component_path = self.path[1:]  # Remove leading '/'
            file_path = os.path.join(os.path.dirname(__file__), component_path)

            # Security check - ensure path is within components directory
            if not component_path.startswith('components/'):
                self.send_error(403, "Access denied")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        except FileNotFoundError:
            self.send_error(404, f"Component file not found: {self.path}")
        except Exception as e:
            logger.error(f"Error serving component file {self.path}: {e}")
            self.send_error(500, f"Internal server error: {e}")

    def serve_static_file(self):
        """Serve static files (CSS, JS, assets)"""
        try:
            # Remove leading slash and get relative path
            static_path = self.path[1:]  # Remove leading '/'
            file_path = os.path.join(os.path.dirname(__file__), static_path)

            # Determine content type
            if static_path.endswith('.css'):
                content_type = 'text/css'
            elif static_path.endswith('.js'):
                content_type = 'application/javascript'
            elif static_path.endswith('.html'):
                content_type = 'text/html'
            elif static_path.endswith('.json'):
                content_type = 'application/json'
            else:
                content_type = 'text/plain'

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-type', f'{content_type}; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        except FileNotFoundError:
            self.send_error(404, f"Static file not found: {self.path}")
        except Exception as e:
            logger.error(f"Error serving static file {self.path}: {e}")
            self.send_error(500, f"Internal server error: {e}")

    def handle_status(self):
        """Check system status"""
        status = {
            'status': self.components.get('status', 'unknown'),
            'components': {
                'llm_client': self.components.get('llm_client') is not None,
                'rag_system': self.components.get('rag_system') is not None
            },
            'timestamp': time.time()
        }
        self.send_json_response(status)

    def handle_get_file_content(self):
        """Handle file content requests with session awareness"""
        try:
            # Parse query parameters
            from urllib.parse import urlparse, parse_qs
            from app.handlers.session_result_manager import get_session_file_loader

            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            file_param = query_params.get('file', [])
            session_id = query_params.get('session_id', [None])[0]

            if not file_param:
                self.send_error(400, "File parameter is required")
                return

            file_path = file_param[0]

            # Enhanced session-aware file loading
            if session_id:
                logger.info(f"📄 Session-aware file request: {file_path} (session: {session_id})")

                # CRITICAL FIX: Add debug info about session directory
                session_dir = f"outputs/execution_{session_id}"
                logger.info(f"🔍 Looking for file in session directory: {session_dir}")
                logger.info(f"🔍 Session directory exists: {os.path.exists(session_dir)}")

                if os.path.exists(session_dir):
                    import glob
                    files_in_dir = glob.glob(os.path.join(session_dir, "*"))
                    logger.info(f"🔍 Files in session directory: {[os.path.basename(f) for f in files_in_dir]}")

                file_loader = get_session_file_loader()
                file_content = file_loader.get_file_content(session_id, file_path)

                if file_content is not None:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(file_content.encode('utf-8'))
                    logger.info(f"✅ Served session file: {file_path} ({len(file_content)} chars)")
                    return
                else:
                    logger.warning(f"❌ Session file not found: {file_path} (session: {session_id})")
                    self.send_error(404, "File not found in session")
                    return

            # Security check - only allow files in output directories
            safe_path = os.path.abspath(file_path)
            allowed_dirs = [
                os.path.abspath("output"),
                os.path.abspath("outputs"),  # All outputs directories
                os.path.abspath("./outputs"),  # Relative outputs
                os.path.abspath("cache"),  # Reference project style cache directory
                os.path.abspath("./cache")  # Relative cache
            ]

            # Check if file is in any allowed directory (including session subdirectories)
            is_allowed = any(safe_path.startswith(allowed_dir) for allowed_dir in allowed_dirs)

            # Additional check for session-specific execution directories
            if not is_allowed and "execution_" in file_path:
                # Allow files in execution_* directories under outputs
                execution_pattern = os.path.abspath("outputs")
                if safe_path.startswith(execution_pattern):
                    is_allowed = True
                    logger.info(f"Allowing session file access: {safe_path}")

            if not is_allowed:
                logger.warning(f"Access denied for file: {safe_path}")
                logger.warning(f"Allowed directories: {allowed_dirs}")
                self.send_error(403, "Access denied")
                return

            if not os.path.exists(safe_path):
                logger.warning(f"File not found: {safe_path}")
                self.send_error(404, "File not found")
                return

            # Determine file type and content type
            file_ext = os.path.splitext(safe_path)[1].lower()

            # Handle binary files (images, PDFs)
            if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.pdf']:
                content_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.pdf': 'application/pdf'
                }

                with open(safe_path, 'rb') as f:
                    content = f.read()

                self.send_response(200)
                self.send_header('Content-type', content_types.get(file_ext, 'application/octet-stream'))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            else:
                # Handle text files
                try:
                    with open(safe_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(content.encode('utf-8'))

                except UnicodeDecodeError:
                    # Fallback for binary files not in the list above
                    with open(safe_path, 'rb') as f:
                        content = f.read()

                    self.send_response(200)
                    self.send_header('Content-type', 'application/octet-stream')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)

        except Exception as e:
            logger.error(f"File content error: {e}")
            self.send_error(500, str(e))

    def handle_step1_analyze(self, data: Dict[str, Any]):
        """Step 1: Analyze query and detect domain"""
        try:
            query = data.get('query', '')
            if not query:
                raise ValueError("Query is required")

            logger.info(f"📋 Step 1: Analyzing query: {query[:50]}...")

            # Get RAG results
            rag_results = self._retrieve_rag_templates(query)
            logger.info(f"🔍 RAG results: {len(rag_results)} templates found")
            logger.info(f"🔍 RAG results data: {rag_results}")

            # Detect domain using LLM
            domain = self._detect_domain_with_llm(query, rag_results)

            # Analyze complexity level
            complexity_level = self._analyze_complexity_level(query, rag_results)

            # Map to ADaM dataset
            adam_dataset = self._map_domain_to_adam_dataset(domain)

            response = {
                'success': True,
                'query': query,
                'domain_detected': domain,
                'complexity_level': complexity_level,
                'adam_dataset': adam_dataset,
                'rag_matches': len(rag_results),
                'rag_results': rag_results,  # Include full RAG results for UI display
                'top_template': rag_results[0] if rag_results else None
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Step 1 error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_step2_template(self, data: Dict[str, Any]):
        """Step 2: Generate quality template using existing template agent"""
        try:
            query = data.get('query', '')
            domain = data.get('domain', 'demographics')
            dataset = data.get('dataset', 'adsl')

            logger.info(f"📝 Step 2: Generating template for {domain}/{dataset}")

            # Use template agent for generation
            from agents.template_agent import TemplateAgent
            from app.rag.template_manager import template_manager

            llm_client = self.components.get('llm_client')

            # Initialize template agent with both required arguments
            template_agent = TemplateAgent(llm_client, template_manager)

            # Generate template using agent
            result = template_agent.generate_mock_template(query, dataset, 'table')

            if result.get('success'):
                template_data = result.get('template', {})
                rag_data = result.get('rag_results', {})

                response = {
                    'success': True,
                    'template_content': template_data.get('html', ''),  # Use HTML for display
                    'template_structure': template_data.get('structure', {}),  # Raw structure data
                    'template_title': template_data.get('title', 'Generated Template'),
                    'rag_analysis': {
                        'success': rag_data.get('success', False),
                        'query': rag_data.get('query', ''),
                        'examples_count': rag_data.get('count', 0),
                        'examples': rag_data.get('examples', [])
                    },
                    'generation_time': result.get('duration', 0),
                    'domain': domain,
                    'dataset': dataset
                }
            else:
                response = {
                    'success': False,
                    'error': result.get('error', 'Template generation failed')
                }

            self.send_json_response(response)

        except Exception as e:
            logger.error(f"Step 2 error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_step3_rcode(self, data: Dict[str, Any]):
        """Step 3: Generate R code using existing code generator agent with session isolation"""
        try:
            template_content = data.get('template_content', '')
            template_structure_data = data.get('template_structure', {})
            domain = data.get('domain', 'demographics')
            dataset = data.get('dataset', 'adsl')
            query = data.get('query', '')
            dataset_info = data.get('dataset_info', {})

            # Extract session information for robust file handling
            execution_id = data.get('execution_id', f"exec_{int(time.time())}")
            session_directory = data.get('session_directory', f"./outputs/execution_{execution_id}")

            logger.info(f"💻 Step 3: Generating R code for {domain}/{dataset}")
            logger.info(f"📁 Session ID: {execution_id}")
            logger.info(f"📊 Dataset info available: {bool(dataset_info)}")
            logger.info(f"📋 Template structure available: {bool(template_structure_data)}")

            # Create session directory for output files
            os.makedirs(session_directory, exist_ok=True)

            # Use code generator agent
            from app.agents.code_generator_agent import CodeGeneratorAgent
            from app.rag.vector_store import vector_store

            llm_client = self.components.get('llm_client')
            code_agent = CodeGeneratorAgent(llm_client, vector_store)

            # Build dataset path
            dataset_path = os.path.abspath(f"data/adam/{dataset.lower()}.sas7bdat")

            # Use Step 2 template structure if available, otherwise extract from content
            if template_structure_data:
                template_structure = template_structure_data
                template_structure.update({"content": template_content})
                logger.info("✅ Using template structure from Step 2")
            else:
                template_structure = self._extract_step2_template_structure(template_content, domain, dataset)
                logger.info("⚠️ Extracting template structure from HTML content")

            # Extract actual dataset variables from Step 1 exploration
            data_exploration = self._extract_step1_dataset_variables(dataset_info, dataset_path, domain)
            logger.info(f"📊 Found {len(data_exploration.get('relevant_variables', {}).get('all_variables', []))} variables")

            # Generate R code using agent with session context for robust file handling
            result = code_agent.generate_r_code(
                template_structure=template_structure,
                data_exploration=data_exploration,
                user_query=query,
                session_context={
                    'execution_id': execution_id,
                    'session_directory': session_directory,
                    'output_path': session_directory
                }
            )

            if result.get('success'):
                response = {
                    'success': True,
                    'r_code': result.get('r_code', ''),
                    'domain': domain,
                    'dataset': dataset,
                    'execution_id': execution_id,
                    'session_directory': session_directory
                }
            else:
                response = {
                    'success': False,
                    'error': result.get('error', 'R code generation failed'),
                    'execution_id': execution_id
                }

            self.send_json_response(response)

        except Exception as e:
            logger.error(f"Step 3 error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def _extract_step2_template_structure(self, template_content: str, domain: str, dataset: str) -> Dict[str, Any]:
        """Extract template structure from Step 2 generated content"""
        import re

        # Extract table headers from HTML
        th_pattern = r'<th[^>]*>(.*?)</th>'
        headers = re.findall(th_pattern, template_content, re.IGNORECASE | re.DOTALL)
        clean_headers = []
        for header in headers:
            clean_header = re.sub(r'<[^>]+>', '', header).strip()
            if clean_header:
                clean_headers.append(clean_header)

        # Extract table rows from HTML
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows_html = re.findall(tr_pattern, template_content, re.IGNORECASE | re.DOTALL)
        rows = []
        for row_html in rows_html:
            if '<th' not in row_html:  # Skip header rows
                td_pattern = r'<td[^>]*>(.*?)</td>'
                cells = re.findall(td_pattern, row_html, re.IGNORECASE | re.DOTALL)
                if cells:
                    clean_cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
                    if clean_cells:
                        rows.append({"label": clean_cells[0], "data": clean_cells[1:]})

        return {
            "id": f"template_{int(time.time())}",
            "title": f"Table - {domain.title()} Analysis",
            "headers": clean_headers or ["Parameter", "Value"],
            "rows": rows,
            "domain": domain,
            "dataset": dataset,
            "content": template_content
        }

    def _extract_step1_dataset_variables(self, dataset_info: Dict[str, Any], dataset_path: str, domain: str) -> Dict[str, Any]:
        """Extract actual dataset variables from Step 1 exploration results"""

        # Get actual variables from dataset exploration
        dataset_details = dataset_info.get('dataset_info', {})
        variables = dataset_details.get('variables', {})

        # Convert variables dict to list format for processing
        var_list = []
        for var_name, var_info in variables.items():
            var_list.append({
                'name': var_name,
                'type': var_info.get('type', 'unknown'),
                'label': var_info.get('label', var_name),
                'unique_values': var_info.get('unique_values', 0),
                'missing_count': var_info.get('missing_count', 0)
            })

        # Categorize variables by domain
        primary_vars = []
        grouping_vars = []

        for var in var_list:
            var_name = var['name'].upper()

            # Find treatment/grouping variables
            if any(key in var_name for key in ['TRT01A', 'TRT01P', 'ARM', 'ACTARM', 'ARMCD']):
                grouping_vars.append({
                    "name": var['name'],  # Use original case
                    "label": var['label'],
                    "role": "treatment_group"
                })

            # Find domain-specific primary variables
            elif domain == "demographics" and any(key in var_name for key in ['AGE', 'SEX', 'RACE', 'ETHNIC']):
                primary_vars.append({
                    "name": var['name'],
                    "label": var['label'],
                    "role": "demographic_characteristic"
                })
            elif domain == "vital_signs" and any(key in var_name for key in ['VSSTRESN', 'VSTEST', 'VSTESTCD']):
                primary_vars.append({
                    "name": var['name'],
                    "label": var['label'],
                    "role": "vital_sign_measurement"
                })

        return {
            "dataset_info": {
                "name": dataset_details.get('file_path', '').split('/')[-1].replace('.sas7bdat', ''),
                "path": dataset_details.get('file_path', dataset_path),
                "domain": domain,
                "nrows": dataset_details.get('nrows', 0),
                "ncols": dataset_details.get('ncols', 0)
            },
            "relevant_variables": {
                "primary_variables": primary_vars,
                "grouping_variables": grouping_vars,
                "all_variables": var_list
            }
        }

    def _is_internal_file(self, filename: str) -> bool:
        """Check if a file is an internal system file that should not be shown to users"""
        internal_patterns = [
            'conversation_',  # Conversation history files
            'modification_',  # Modification history files
            '.log',          # Log files
            '.tmp',          # Temporary files
            '.cache',        # Cache files
        ]

        # Check if filename starts with or contains internal patterns
        filename_lower = filename.lower()
        for pattern in internal_patterns:
            if pattern in filename_lower:
                return True

        # Also filter out hidden files (starting with .)
        if filename.startswith('.'):
            return True

        return False

    def handle_step4_execute(self, data: Dict[str, Any]):
        """Step 4: Execute R code using enhanced R interpreter with session isolation"""
        try:
            r_code = data.get('r_code', '')
            if not r_code:
                raise ValueError("R code is required")

            # Get session parameters from frontend
            execution_id = data.get('execution_id', f"exec_{int(time.time())}")
            # Use the work_dir directly from frontend - don't create nested directories
            work_dir = data.get('work_dir', f"./outputs/execution_{execution_id}")
            session_isolation = data.get('session_isolation', True)

            # Ensure work_dir is clean (no double nesting)
            if work_dir.count('/execution_') > 1:
                # Fix nested execution directories
                parts = work_dir.split('/')
                # Keep only the last execution directory
                for i, part in enumerate(parts):
                    if part.startswith('execution_'):
                        work_dir = '/'.join(parts[:i+1])
                        break

            logger.info(f"⚡ Step 4: Executing R code ({len(r_code)} chars)")
            logger.info(f"📁 Session ID: {execution_id}")
            logger.info(f"📂 Work directory: {work_dir}")

            # Create session-specific work directory
            os.makedirs(work_dir, exist_ok=True)

            # Use Enhanced Simple R Executor with workspace persistence for session continuity
            from app.handlers.simple_r_executor import SimpleRExecutor

            # Reuse existing R interpreter for session continuity (like Interactive AI Assistant)
            if not hasattr(self.__class__, '_direct_r_interpreters'):
                self.__class__._direct_r_interpreters = {}

            if execution_id not in self.__class__._direct_r_interpreters:
                # Create new R interpreter for this session
                r_interpreter = SimpleRExecutor(work_dir, execution_id)
                r_interpreter.enable_workspace_persistence = True  # Enable session continuity
                self.__class__._direct_r_interpreters[execution_id] = r_interpreter
                logger.info(f"📁 Created new persistent R session: {execution_id}")
            else:
                # Reuse existing R interpreter for session continuity
                r_interpreter = self.__class__._direct_r_interpreters[execution_id]
                logger.info(f"📁 Reusing persistent R session: {execution_id}")

            # Execute R code using Enhanced Simple R Executor
            execution_result = r_interpreter.execute_r_code(r_code)

            # SimpleRExecutor already returns the correct format with:
            # - success: bool
            # - output: str (summary)
            # - error: str
            # - files_generated: list
            # - execution_time: float
            # - timestamp: float
            # SimpleRExecutor already provides all needed data, just use it directly
            files_generated = execution_result.get('files_generated', [])
            logger.info(f"📄 SimpleRExecutor found {len(files_generated)} generated files: {files_generated}")

            # Prepare response using SimpleRExecutor results
            response = {
                'success': execution_result.get('success', False),
                'output': execution_result.get('output', ''),
                'error': execution_result.get('error', ''),
                'execution_time': execution_result.get('execution_time', 0),
                'files_generated': files_generated,
                'execution_id': execution_id,
                'output_directory': execution_result.get('output_directory', work_dir),
                'session_isolation': session_isolation
            }

            logger.info(f"✅ Execution completed: {len(files_generated)} files generated")
            self.send_json_response(response)

        except Exception as e:
            logger.error(f"Step 4 error: {e}")
            self.send_json_response({
                'success': False,
                'error': str(e),
                'execution_id': data.get('execution_id', 'unknown'),
                'files_generated': []
            })

    def handle_explore_dataset(self, data: Dict[str, Any]):
        """Handle dataset exploration requests"""
        try:
            dataset_path = data.get('dataset_path', '')
            if not dataset_path:
                raise ValueError("Dataset path is required")

            logger.info(f"📊 Exploring dataset: {dataset_path}")

            # Use data explorer agent
            from agents.data_explorer_agent import DataExplorerAgent
            from r_integration.enhanced_r_interpreter import EnhancedRInterpreter

            r_interpreter = EnhancedRInterpreter()
            llm_client = self.components.get('llm_client')
            data_explorer = DataExplorerAgent(llm_client, r_interpreter)

            # Perform dataset exploration
            result = data_explorer.explore_dataset(dataset_path, {})

            self.send_json_response(result)

        except Exception as e:
            logger.error(f"Dataset exploration error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_validate_rcode(self, data: Dict[str, Any]):
        """Handle R code validation requests"""
        try:
            r_code = data.get('r_code', '')
            if not r_code:
                raise ValueError("R code is required")

            logger.info(f"✅ Validating R code ({len(r_code)} chars)")

            # Use existing R interpreter for validation
            from r_integration.enhanced_r_interpreter import EnhancedRInterpreter

            r_interpreter = EnhancedRInterpreter()
            result = r_interpreter.validate_code(r_code)

            self.send_json_response(result)

        except Exception as e:
            logger.error(f"R code validation error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_debug_code(self, data: Dict[str, Any]):
        """Handle code debugging requests"""
        try:
            r_code = data.get('r_code', '')
            error_message = data.get('error_message', '')

            if not r_code:
                raise ValueError("R code is required")

            logger.info(f"🐛 Debugging R code error")

            # Use debug agent
            from agents.debug_agent import DebugAgent

            llm_client = self.components.get('llm_client')
            debug_agent = DebugAgent(llm_client)

            error_info = {
                "has_error": True,
                "error_message": error_message,
                "error_type": "runtime"
            }

            result = debug_agent.debug_code_error(r_code, error_info)
            self.send_json_response(result)

        except Exception as e:
            logger.error(f"Code debugging error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_debug_chat(self, data: Dict[str, Any]):
        """Handle debug chat requests"""
        try:
            message = data.get('message', '')
            context = data.get('context', {})

            if not message:
                raise ValueError("Message is required")

            logger.info(f"💬 Debug chat: {message[:50]}...")

            # Use assistant agent for chat
            from agents.assistant_agent import AssistantAgent

            llm_client = self.components.get('llm_client')
            assistant = AssistantAgent(llm_client)

            result = assistant.handle_user_query(message, context)

            self.send_json_response(result)

        except Exception as e:
            logger.error(f"Debug chat error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_explain_rcode(self, data: Dict[str, Any]):
        """Handle R code explanation requests"""
        try:
            r_code = data.get('r_code', '')
            if not r_code:
                raise ValueError("R code is required")

            logger.info(f"📖 Explaining R code ({len(r_code)} chars)")

            # Use code generator agent for explanation
            from agents.code_generator_agent import CodeGeneratorAgent

            llm_client = self.components.get('llm_client')
            code_agent = CodeGeneratorAgent(llm_client)

            result = code_agent.explain_code(r_code)

            self.send_json_response(result)

        except Exception as e:
            logger.error(f"R code explanation error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    # ==================== Helper Methods ====================

    def _retrieve_rag_templates(self, query: str) -> list:
        """Retrieve relevant templates using RAG"""
        try:
            rag_system = self.components.get('rag_system')
            logger.info(f"🔍 RAG system available: {rag_system is not None}")

            if rag_system:
                results = rag_system.retrieve_relevant_templates(query, top_k=5)
                logger.info(f"🔍 RAG raw results: {results}")
                logger.info(f"🔍 RAG results type: {type(results)}")

                if results and isinstance(results, list):
                    filtered_results = results[:3]
                    logger.info(f"🔍 RAG filtered results: {filtered_results}")
                    return filtered_results
            else:
                logger.warning("🔍 RAG system not available in components")
        except Exception as e:
            logger.warning(f"RAG retrieval error: {e}")
        return []

    def _detect_domain_with_llm(self, query: str, rag_results: list) -> str:
        """Detect domain using LLM analysis"""
        try:
            llm_client = self.components.get('llm_client')
            if not llm_client:
                return "demographics"

            # Build context from RAG results
            rag_context = ""
            if rag_results:
                rag_context = "Retrieved templates:\n"
                for template in rag_results[:3]:
                    title = template.get('title', 'Unknown')
                    rag_context += f"- {title}\n"

            prompt = f"""Analyze this clinical query and determine the domain:

Query: "{query}"
{rag_context}

Determine which domain this belongs to:
- demographics: Patient baseline characteristics
- adverse_events: Safety data, AEs
- vital_signs: Vital signs measurements  
- laboratory: Lab values, tests
- efficacy: Treatment effectiveness

Respond with ONLY the domain name."""

            if hasattr(llm_client, '_try_claude') and llm_client.anthropic_client:
                response = llm_client._try_claude(prompt, max_tokens=50, temperature=0.1)
            else:
                response = llm_client.generate_response(prompt, max_tokens=50, temperature=0.1)

            content = response.get('content', '') if isinstance(response, dict) else str(response)
            
            # Parse domain from response
            for domain in ['demographics', 'adverse_events', 'vital_signs', 'laboratory', 'efficacy']:
                if domain in content.lower():
                    return domain
                    
            return "demographics"  # Default
            
        except Exception as e:
            logger.error(f"Domain detection error: {e}")
            return "demographics"

    def _map_domain_to_adam_dataset(self, domain: str) -> str:
        """Map clinical domain to ADaM dataset name"""
        mapping = {
            'demographics': 'adsl',
            'adverse_events': 'adae',
            'vital_signs': 'advs',
            'laboratory': 'adlb',
            'efficacy': 'adtte'
        }
        return mapping.get(domain, 'adsl')

    def _analyze_complexity_level(self, query: str, rag_results: list) -> str:
        """Analyze query complexity level using LLM"""
        try:
            llm_client = self.components.get('llm_client')
            if not llm_client:
                return "medium"

            # Build context from RAG results
            rag_context = ""
            if rag_results:
                rag_context = "Similar templates found:\n"
                for template in rag_results[:3]:
                    title = template.get('title', 'Unknown')
                    similarity = template.get('similarity', 0)
                    rag_context += f"- {title} (similarity: {similarity:.3f})\n"

            prompt = f"""Analyze this clinical query and determine its complexity level:

Query: "{query}"
{rag_context}

Consider these factors:
- Number of variables/parameters needed
- Statistical complexity (simple counts vs complex analyses)
- Data transformation requirements
- Regulatory compliance needs
- Cross-tabulation complexity

Determine complexity level:
- simple: Basic counts, frequencies, single variable summaries
- medium: Cross-tabulations, basic statistics, standard clinical tables
- complex: Advanced statistics, multiple endpoints, complex derivations

Respond with ONLY the complexity level (simple/medium/complex)."""

            if hasattr(llm_client, '_try_claude') and llm_client.anthropic_client:
                response = llm_client._try_claude(prompt, max_tokens=50, temperature=0.1)
            else:
                response = llm_client.generate_response(prompt, max_tokens=50, temperature=0.1)

            content = response.get('content', '') if isinstance(response, dict) else str(response)

            # Extract complexity level
            content_lower = content.lower().strip()
            if 'simple' in content_lower:
                return 'simple'
            elif 'complex' in content_lower:
                return 'complex'
            else:
                return 'medium'

        except Exception as e:
            logger.warning(f"Complexity analysis error: {e}")
            return "medium"



    def handle_set_llm_provider(self, data: Dict[str, Any]):
        """Set the LLM provider"""
        try:
            provider = data.get('provider', '').lower()

            if not provider:
                self.send_json_response({'success': False, 'error': 'Provider not specified'})
                return

            llm_client = self.components.get('llm_client')
            if not llm_client:
                self.send_json_response({'success': False, 'error': 'LLM client not available'})
                return

            # Set the provider
            llm_client.set_provider(provider)

            logger.info(f"🔄 LLM provider changed to: {provider}")

            self.send_json_response({
                'success': True,
                'provider': provider,
                'message': f'LLM provider changed to {provider}'
            })

        except Exception as e:
            logger.error(f"Set LLM provider error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_get_llm_providers(self, data: Dict[str, Any]):
        """Get available LLM providers"""
        try:
            llm_client = self.components.get('llm_client')
            if not llm_client:
                self.send_json_response({'success': False, 'error': 'LLM client not available'})
                return

            available_providers = llm_client.get_available_providers()
            current_provider = llm_client.get_current_provider()

            self.send_json_response({
                'success': True,
                'available_providers': available_providers,
                'current_provider': current_provider
            })

        except Exception as e:
            logger.error(f"Get LLM providers error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def send_json_response(self, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    # ===== INTERACTIVE STEP 4 HANDLERS =====

    def handle_step4_interactive_initialize(self, data: Dict[str, Any]):
        """Initialize interactive R session"""
        try:
            # Initialize interactive handler if not exists - USING REFERENCE PROJECT STYLE
            if not hasattr(self.__class__, '_interactive_handler'):
                # Add the project root to Python path
                import sys
                import os
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)

                from app.handlers.r_reference_handler import RReferenceHandler
                llm_client = self.components.get('llm_client')

                if not llm_client:
                    raise RuntimeError("LLM client not available")

                # Get work directory from request
                work_dir = data.get('work_dir', './outputs/step4')

                # Create session context for RReferenceHandler
                import time
                session_context = {
                    'execution_id': f"step4_{int(time.time())}",
                    'work_dir': work_dir,
                    'session_directory': work_dir
                }

                # CRITICAL FIX: Pass the shared LLM client to Step 4 instead of letting it create its own
                # This ensures Step 4 respects user's LLM provider selection
                self.__class__._interactive_handler = RReferenceHandler(llm_client, session_context)
                logger.info(f"🔍 Step 4 handler initialized with SHARED provider: {llm_client.get_current_provider()}")
                logger.info(f"🔍 Session context: {session_context}")

            # The RReferenceHandler is already initialized in the constructor
            # Just return success with session info
            result = {
                'success': True,
                'message': 'Interactive session initialized successfully',
                'session_info': {
                    'execution_id': self.__class__._interactive_handler.execution_id,
                    'work_dir': self.__class__._interactive_handler.work_dir,
                    'provider': self.__class__._interactive_handler.llm_client.get_current_provider()
                }
            }

            self.send_json_response(result)

        except Exception as e:
            logger.error(f"Interactive initialization error: {e}")
            self.send_json_response({
                'success': False,
                'error': str(e),
                'message': 'Failed to initialize interactive session'
            })

    def handle_step4_interactive_chat(self, data: Dict[str, Any]):
        """Handle interactive chat with streaming response (REFERENCE PROJECT STYLE)"""
        try:
            # CRITICAL FIX: Create fresh handler for each request to prevent state corruption
            # Add the project root to Python path
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            # Create fresh handler for each request
            from app.handlers.r_reference_handler import RReferenceHandler

            logger.info(f"🔍 Components available: {hasattr(self, 'components')}")
            logger.info(f"🔍 Class components available: {hasattr(self.__class__, '_components')}")

            if hasattr(self, 'components'):
                llm_client = self.components.get('llm_client')
                logger.info(f"🔍 LLM client from components: {llm_client is not None}")
            else:
                logger.error("🔍 No components property available")
                raise RuntimeError("Components not initialized")

            if not llm_client:
                raise RuntimeError("LLM client not available")

            message = data.get('message', '')
            context = data.get('context', {})

            # CRITICAL DEBUG: Log the context to see what's being received
            logger.info(f"🔍 BACKEND: Received message: {message[:100]}...")
            logger.info(f"🔍 BACKEND: Context keys: {list(context.keys())}")
            logger.info(f"🔍 BACKEND: Current code in context: {bool(context.get('current_code'))}")
            if context.get('current_code'):
                current_code = context.get('current_code', '')
                logger.info(f"🔍 BACKEND: Current code length: {len(current_code)}")
                logger.info(f"🔍 BACKEND: Current code preview: {current_code[:100]}...")
            else:
                logger.warning(f"🔍 BACKEND: NO CURRENT CODE FOUND IN CONTEXT!")
                logger.info(f"🔍 BACKEND: Full context: {context}")

            # Extract session information for robust file handling
            execution_id_from_context = context.get('execution_id')
            logger.info(f"🔍 BACKEND: execution_id from context: {execution_id_from_context}")

            if execution_id_from_context:
                execution_id = execution_id_from_context
                logger.info(f"🔄 BACKEND: Using existing session ID: {execution_id}")
            else:
                execution_id = f"exec_{int(time.time())}"
                logger.info(f"🆕 BACKEND: Created new session ID: {execution_id}")

            session_directory = context.get('session_directory', f"./outputs/execution_{execution_id}")

            # Create session directory
            os.makedirs(session_directory, exist_ok=True)

            # PHASE 2: Use session pool for persistent handlers
            from app.handlers.session_pool import get_session_pool
            session_pool = get_session_pool()

            # Get or create persistent session
            persistent_mode = True  # Enable persistent mode for Step 4 Interactive
            session_context = {
                'execution_id': execution_id,
                'session_directory': session_directory,
                'work_dir': session_directory,
                'persistent_mode': persistent_mode
            }

            handler = session_pool.get_or_create_session(
                session_id=execution_id,
                llm_client=llm_client,
                session_context=session_context
            )

            # PHASE 4: Enhanced session state management
            session_pool.mark_session_busy(execution_id)
            session_pool.increment_request_count(execution_id)

            logger.info(f"🔍 Using persistent handler for session: {execution_id}")
            logger.info(f"📁 Session ID: {execution_id}")
            logger.info(f"📂 Session directory: {session_directory}")

            # Set Server-Sent Events headers (what the HTML expects)
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # PHASE 3: Enhanced connection management
            from app.handlers.connection_manager import get_connection_manager, EnhancedSSEStreamer
            from app.handlers.session_result_manager import get_session_result_manager

            connection_manager = get_connection_manager()
            result_manager = get_session_result_manager()

            # Register connection
            connection_manager.register_connection(execution_id, self)

            # Create enhanced SSE streamer
            sse_streamer = EnhancedSSEStreamer(self, execution_id, connection_manager)

            logger.info(f"🔍 BACKEND: Starting enhanced SSE stream for session {execution_id}")
            logger.info(f"🔍 BACKEND: Handler type: {type(handler)}")
            logger.info(f"🔍 BACKEND: Message: {message[:100]}...")

            try:
                # Use enhanced streaming with better connection management
                # Enhanced streaming handles all event processing, timeouts, and connection management
                for success in sse_streamer.stream_handler_events(handler, message, context):
                    if not success:
                        logger.warning(f"⚠️ BACKEND: Stream event failed for session {execution_id}")
                        break

                # Get final stream statistics
                stream_stats = sse_streamer.get_stream_stats()
                logger.info(f"🔍 BACKEND: Stream completed for session {execution_id}: {stream_stats['event_count']} events in {stream_stats['duration_seconds']:.1f}s")
            except Exception as e:
                logger.error(f"❌ BACKEND: Error during enhanced streaming: {e}")
                import traceback
                logger.error(f"❌ BACKEND: Traceback: {traceback.format_exc()}")
                # Send error event through enhanced streamer
                sse_streamer.send_event('error', f"Processing error: {str(e)}")

            finally:
                # Mark session as ready for next request
                session_pool.mark_session_ready(execution_id)

                if persistent_mode:
                    # CRITICAL FIX: Send persistent_mode event to frontend
                    logger.info(f"🔄 BACKEND: Sending persistent_mode event to frontend")
                    sse_streamer.send_event('persistent_mode', {
                        'session_id': execution_id,
                        'status': 'active',
                        'message': 'Session ready for continuous conversation'
                    })

                    # MODIFIED APPROACH: Don't keep HTTP request alive, just keep session in pool
                    logger.info(f"🔄 BACKEND: Persistent session {execution_id} kept alive in pool and marked ready")
                    logger.info(f"🔄 BACKEND: Session available for follow-up requests via new HTTP connections")
                    logger.info(f"🔄 BACKEND: Session ready for continuous conversation")

                    # Clean up this connection but keep session alive for reuse
                    connection_manager.cleanup_connection(execution_id)
                    logger.info(f"🔍 BACKEND: Persistent session HTTP request completed - session remains in pool")
                    return
                else:
                    # Non-persistent mode: clean up connection and session
                    connection_manager.cleanup_connection(execution_id)
                    logger.info(f"🔍 BACKEND: Non-persistent session {execution_id} completed and connection cleaned up")
                    logger.info(f"🔍 BACKEND: Enhanced SSE handler completed")
                    return

        except Exception as e:
            logger.error(f"❌ BACKEND: Critical error in handle_step4_interactive_chat: {e}")
            logger.error(f"❌ BACKEND: Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ BACKEND: Traceback: {traceback.format_exc()}")
            self.handle_step4_interactive_error_handler(e)

    # NOTE: _enter_persistent_sse_mode function removed as we use simplified session reuse architecture

    def handle_step4_interactive_error_handler(self, e: Exception):
        """Handle errors in interactive chat"""
        logger.error(f"Interactive chat error: {e}")
        try:
            error_event = {
                'type': 'error',
                'content': f'Chat error: {str(e)}',
                'timestamp': time.time()
            }
            event_data = f"data: {json.dumps(error_event)}\n\n"
            self.wfile.write(event_data.encode())
            self.wfile.flush()

            # Send end event after error
            end_event = f"data: {json.dumps({'type': 'end'})}\n\n"
            self.wfile.write(end_event.encode())
            self.wfile.flush()
            logger.info(f"🔍 BACKEND: Error handler completed, returning to close connection")
        except (BrokenPipeError, ConnectionResetError, OSError):
            logger.warning("⚠️ BACKEND: Could not send error event - client disconnected")

        # CRITICAL FIX: Return to properly close the SSE connection after error
        return

    def handle_step4_interactive_interrupt(self, data: Dict[str, Any]):
        """Interrupt current execution"""
        try:
            if hasattr(self.__class__, '_interactive_handler'):
                result = self.__class__._interactive_handler.interrupt_execution()
                self.send_json_response(result)
            else:
                self.send_json_response({'success': False, 'message': 'No active session'})
        except Exception as e:
            logger.error(f"Interactive interrupt error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_step4_interactive_restart(self, data: Dict[str, Any]):
        """Restart interactive session"""
        try:
            if hasattr(self.__class__, '_interactive_handler'):
                result = self.__class__._interactive_handler.restart_session()
                self.send_json_response(result)
            else:
                self.send_json_response({'success': False, 'message': 'No active session'})
        except Exception as e:
            logger.error(f"Interactive restart error: {e}")
            self.send_json_response({'success': False, 'error': str(e)})


def main():
    """Start the production backend server"""
    PORT = 8008
    
    print("🎯 PRODUCTION CLINICAL TLF BACKEND")
    print("=" * 50)
    print(f"🌐 Starting on port {PORT}")
    print(f"📍 Access UI at: http://localhost:{PORT}")
    print("🔬 Production AI components only")
    print()
    
    try:
        # Use ThreadingTCPServer for concurrent request handling
        with socketserver.ThreadingTCPServer(("", PORT), ProductionBackendHandler) as httpd:
            httpd.allow_reuse_address = True  # Prevent "Address already in use" errors
            print(f"✅ Multi-threaded server running at http://localhost:{PORT}")
            print("🔄 Server can handle concurrent requests")
            print("Press Ctrl+C to stop")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")


if __name__ == "__main__":
    main()
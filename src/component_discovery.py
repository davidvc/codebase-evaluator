"""Module for discovering components and their relationships in Java/Maven projects."""

import os
import re
import json
import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import hashlib
from datetime import datetime
from src.types import AnalysisState


class ComponentDiscoveryError(Exception):
    """Base exception for component discovery errors."""
    pass


class InvalidComponentError(ComponentDiscoveryError):
    """Raised when a component is invalid or malformed."""
    pass


class CacheError(ComponentDiscoveryError):
    """Raised when there's an error with the component cache."""
    pass


@dataclass
class Component:
    """Represents a discovered component.
    
    Attributes:
        name: Unique name of the component
        package: Java package name
        path: File system path to component
        source_files: List of Java source files
        dependencies: Set of package names this component depends on
        is_test: Whether this is a test component
        metadata: Additional component information
    """
    name: str
    package: str
    path: str
    source_files: List[str]
    dependencies: Set[str]
    is_test: bool
    metadata: Dict

    def __post_init__(self):
        """Validate component attributes."""
        if not self.name or not isinstance(self.name, str):
            raise InvalidComponentError("Component name must be a non-empty string")
        if not self.package or not isinstance(self.package, str):
            raise InvalidComponentError("Package name must be a non-empty string")
        if not os.path.exists(self.path):
            raise InvalidComponentError(f"Component path does not exist: {self.path}")


class DependencyGraph:
    """Represents component dependencies using an adjacency list."""
    
    def __init__(self):
        """Initialize empty dependency graph."""
        self._forward = defaultdict(set)  # component -> dependencies
        self._reverse = defaultdict(set)  # component -> dependents
        
    def add_node(self, component: str):
        """Add a component to the graph."""
        if component not in self._forward:
            self._forward[component] = set()
            self._reverse[component] = set()
            
    def add_edge(self, from_component: str, to_component: str):
        """Add a dependency edge between components."""
        self._forward[from_component].add(to_component)
        self._reverse[to_component].add(from_component)
        
    def get_dependencies(self, component: str) -> Set[str]:
        """Get components that the given component depends on."""
        return self._forward.get(component, set())
        
    def get_dependents(self, component: str) -> Set[str]:
        """Get components that depend on the given component."""
        return self._reverse.get(component, set())
        
    def has_cycles(self) -> bool:
        """Check for circular dependencies."""
        visited = set()
        path = set()
        
        def visit(component: str) -> bool:
            if component in path:
                return True
            if component in visited:
                return False
                
            visited.add(component)
            path.add(component)
            
            for dep in self._forward[component]:
                if visit(dep):
                    return True
                    
            path.remove(component)
            return False
            
        return any(visit(component) for component in self._forward)


class ComponentCache:
    """Handles caching of discovered components."""
    
    def __init__(self, cache_dir: str = ".component_cache", max_size_mb: int = 100):
        """Initialize component cache.
        
        Args:
            cache_dir: Directory to store cache files
            max_size_mb: Maximum cache size in megabytes
        """
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.cache_dir.mkdir(exist_ok=True)
        
    def _get_cache_key(self, repo_path: str) -> str:
        """Generate cache key from repository path and contents."""
        hasher = hashlib.sha256()
        hasher.update(repo_path.encode())
        
        # Include last modified times of Java files
        for root, _, files in os.walk(repo_path):
            for file in sorted(files):
                if file.endswith('.java'):
                    path = os.path.join(root, file)
                    mtime = os.path.getmtime(path)
                    hasher.update(f"{path}:{mtime}".encode())
                    
        return hasher.hexdigest()
        
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a key."""
        return self.cache_dir / f"components_{cache_key}.json"
        
    def _cleanup_old_cache(self):
        """Remove old cache files if total size exceeds limit."""
        cache_files = []
        total_size = 0
        
        for file in self.cache_dir.glob("components_*.json"):
            size = file.stat().st_size
            mtime = file.stat().st_mtime
            cache_files.append((file, size, mtime))
            total_size += size
            
        if total_size > self.max_size:
            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda x: x[2])
            
            # Remove old files until under limit
            for file, size, _ in cache_files:
                if total_size <= self.max_size:
                    break
                file.unlink()
                total_size -= size
                
    def load(self, repo_path: str) -> Optional[Tuple[Dict[str, Component], DependencyGraph]]:
        """Load components from cache if available and valid."""
        try:
            cache_key = self._get_cache_key(repo_path)
            cache_path = self._get_cache_path(cache_key)
            
            if not cache_path.exists():
                return None
                
            with open(cache_path, 'r') as f:
                data = json.load(f)
                
            # Validate cache format and version
            if data.get('version') != '1.0':
                return None
                
            # Reconstruct components
            components = {}
            for comp_data in data['components']:
                try:
                    components[comp_data['name']] = Component(
                        name=comp_data['name'],
                        package=comp_data['package'],
                        path=comp_data['path'],
                        source_files=comp_data['source_files'],
                        dependencies=set(comp_data['dependencies']),
                        is_test=comp_data['is_test'],
                        metadata=comp_data['metadata']
                    )
                except (KeyError, InvalidComponentError) as e:
                    logging.warning(f"Invalid component in cache: {str(e)}")
                    return None
                    
            # Reconstruct dependency graph
            graph = DependencyGraph()
            for edge in data['edges']:
                try:
                    from_comp, to_comp = edge
                    graph.add_node(from_comp)
                    graph.add_node(to_comp)
                    graph.add_edge(from_comp, to_comp)
                except (ValueError, TypeError) as e:
                    logging.warning(f"Invalid edge in cache: {str(e)}")
                    return None
                    
            return components, graph
            
        except (json.JSONDecodeError, KeyError) as e:
            raise CacheError(f"Failed to load cache: {str(e)}") from e
        except Exception as e:
            logging.warning(f"Unexpected error loading cache: {str(e)}")
            return None
            
    def save(self, repo_path: str, components: Dict[str, Component], graph: DependencyGraph):
        """Save components to cache."""
        try:
            self._cleanup_old_cache()
            
            cache_key = self._get_cache_key(repo_path)
            cache_path = self._get_cache_path(cache_key)
            
            # Prepare serializable data
            data = {
                'version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'components': [
                    {
                        'name': comp.name,
                        'package': comp.package,
                        'path': comp.path,
                        'source_files': comp.source_files,
                        'dependencies': list(comp.dependencies),
                        'is_test': comp.is_test,
                        'metadata': comp.metadata
                    }
                    for comp in components.values()
                ],
                'edges': [
                    [from_comp, to_comp]
                    for from_comp in components
                    for to_comp in graph.get_dependencies(from_comp)
                ]
            }
            
            # Write to temporary file first
            temp_path = cache_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            # Atomic rename
            temp_path.replace(cache_path)
            
        except Exception as e:
            raise CacheError(f"Failed to save cache: {str(e)}") from e


class JavaFileAnalyzer:
    """Analyzes Java source files for packages and dependencies."""
    
    @staticmethod
    def extract_package(content: str) -> Optional[str]:
        """Extract package name from Java file content."""
        match = re.search(r'package\s+([\w.]+);', content)
        return match.group(1) if match else None
        
    @staticmethod
    def find_dependencies(content: str) -> Set[str]:
        """Find package dependencies in Java file content."""
        dependencies = set()
        
        # Find import statements
        imports = re.finditer(r'import\s+([\w.]+)(?:\s*\*)?;', content)
        for match in imports:
            package = match.group(1)
            # Get base package (up to second-to-last dot)
            parts = package.split('.')
            if len(parts) > 1:
                dependencies.add('.'.join(parts[:-1]))
                
        return dependencies
        
    @staticmethod
    def extract_metadata(content: str) -> Dict:
        """Extract metadata from Java file content."""
        return {
            'has_interfaces': bool(re.search(r'\binterface\s+\w+', content)),
            'has_abstract_classes': bool(re.search(r'\babstract\s+class\s+\w+', content)),
            'is_test': bool(re.search(r'@Test\b|Test\w+\.java$|test|Test', content)),
            'line_count': len(content.splitlines())
        }


def discover_components(state: AnalysisState) -> dict:
    """Identify key components and their relationships.
    
    Args:
        state: Current analysis state containing repo path
        
    Returns:
        Updated state with component analysis results
        
    Raises:
        ComponentDiscoveryError: If component discovery fails
    """
    messages = list(state.get("messages", []))
    messages.append("Starting component discovery...")
    
    try:
        repo_path = state.get("repo_path")
        if not repo_path:
            raise ComponentDiscoveryError("Repository path not found in state")
            
        cache = ComponentCache()
        
        # Try loading from cache first
        cached = cache.load(repo_path)
        if cached:
            components, graph = cached
            messages.append("Loaded component graph from cache")
            return {
                **state,
                "messages": messages,
                "components": components,
                "dependency_graph": graph
            }
            
        # Initialize containers
        components: Dict[str, Component] = {}
        graph = DependencyGraph()
        file_analyzer = JavaFileAnalyzer()
        
        # Process main and test source directories
        for src_type in ['main', 'test']:
            src_dir = os.path.join(repo_path, f"src/{src_type}/java")
            if not os.path.exists(src_dir):
                continue
                
            # First pass: collect all Java files and their contents
            java_files = []
            for root, _, files in os.walk(src_dir):
                for file in files:
                    if file.endswith('.java'):
                        try:
                            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                content = f.read()
                            java_files.append((root, file, content))
                        except UnicodeDecodeError:
                            messages.append(f"Skipping binary file: {file}")
                            continue
                        except Exception as e:
                            messages.append(f"Error reading {file}: {str(e)}")
                            continue
                            
            # Group files by package
            package_files = defaultdict(list)
            for root, file, content in java_files:
                package = file_analyzer.extract_package(content)
                if package:
                    package_files[package].append((root, file, content))
                    
            # Create components
            for package, files in package_files.items():
                try:
                    # Aggregate metadata
                    metadata = defaultdict(int)
                    dependencies = set()
                    source_files = []
                    
                    for root, file, content in files:
                        file_path = os.path.join(root, file)
                        source_files.append(file_path)
                        
                        # Analyze file
                        file_meta = file_analyzer.extract_metadata(content)
                        file_deps = file_analyzer.find_dependencies(content)
                        
                        # Update component metadata
                        metadata['file_count'] += 1
                        metadata['total_lines'] += file_meta['line_count']
                        metadata['has_interfaces'] |= file_meta['has_interfaces']
                        metadata['has_abstract_classes'] |= file_meta['has_abstract_classes']
                        metadata['has_tests'] |= file_meta['is_test']
                        
                        dependencies.update(file_deps)
                        
                    # Create component
                    name = package.split('.')[-1]
                    if src_type == 'test':
                        name = f"{name}Test"
                        
                    component = Component(
                        name=name,
                        package=package,
                        path=os.path.dirname(source_files[0]),
                        source_files=source_files,
                        dependencies=dependencies,
                        is_test=(src_type == 'test'),
                        metadata=dict(metadata)
                    )
                    
                    components[component.name] = component
                    graph.add_node(component.name)
                    
                except InvalidComponentError as e:
                    messages.append(f"Skipping invalid component {package}: {str(e)}")
                    continue
                    
        # Add dependency edges
        for component in components.values():
            for dep in component.dependencies:
                # Find matching component by package
                for other in components.values():
                    if other.package.startswith(dep):
                        graph.add_edge(component.name, other.name)
                        
        # Check for circular dependencies
        if graph.has_cycles():
            messages.append("Warning: Circular dependencies detected")
            
        # Cache the results
        cache.save(repo_path, components, graph)
        
        messages.append(f"Discovered {len(components)} components")
        return {
            **state,
            "messages": messages,
            "components": components,
            "dependency_graph": graph
        }
        
    except Exception as e:
        messages.append(f"Error during component discovery: {str(e)}")
        raise ComponentDiscoveryError(str(e)) from e

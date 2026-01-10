import os
import ast

def get_imports(file_path):
    """Bir python dosyasındaki tüm importları bulur."""
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            root = ast.parse(f.read(), filename=file_path)
        
        for node in ast.walk(root):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except Exception as e:
        pass
    return imports

def scan_project(start_path):
    print(f"--- PROJE ANALİZ RAPORU: {os.path.basename(os.getcwd())} ---")
    print("\n[DOSYA AĞACI]")
    
    all_imports = set()
    
    for root, dirs, files in os.walk(start_path):
        # venv, .git, __pycache__, dist, build klasörlerini atla
        dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__', 'dist', 'build', 'idea']]
        
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f"{indent}|-- {os.path.basename(root)}/")
        
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{sub_indent}|-- {f}")
            if f.endswith(".py"):
                file_imports = get_imports(os.path.join(root, f))
                all_imports.update(file_imports)

    print("\n[TESPİT EDİLEN TÜM KÜTÜPHANELER (IMPORTS)]")
    print(", ".join(sorted(all_imports)))
    print("-" * 50)

if __name__ == "__main__":
    scan_project(".")
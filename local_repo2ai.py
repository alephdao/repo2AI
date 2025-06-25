import os
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
from typing import Optional, List

def describe_repo_contents_xml(repo_folder: str, output_path: str, exclude_folders: Optional[List[str]] = None, exclude_files: Optional[List[str]] = None):
    """
    Generate XML description of repository structure and contents
    """
    if exclude_folders is None:
        exclude_folders = []
    if exclude_files is None:
        exclude_files = []
    
    def should_exclude_path(path: str, repo_folder: str) -> bool:
        """Check if a path should be excluded based on exclusion rules"""
        rel_path = os.path.relpath(path, repo_folder)
        
        # Check if this specific file should be excluded
        if os.path.isfile(path):
            for exclude_file in exclude_files:
                if rel_path == exclude_file or rel_path.endswith('/' + exclude_file):
                    return True
        
        # Check if this directory or any parent directory should be excluded
        path_parts = rel_path.split(os.sep)
        for exclude_folder in exclude_folders:
            exclude_parts = exclude_folder.split('/')
            
            # Check if the current path matches the exclusion pattern
            if len(path_parts) >= len(exclude_parts):
                # Check if any segment of the path matches the exclusion pattern
                for i in range(len(path_parts) - len(exclude_parts) + 1):
                    if path_parts[i:i+len(exclude_parts)] == exclude_parts:
                        return True
        
        return False
    
    def build_structure_xml(parent_element, path, level=0):
        """Recursively build XML structure"""
        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            # Skip directories we can't read
            print(f"Skipping directory (no permission): {path}")
            return
            
        for item in items:
            # Skip hidden files and common ignore patterns
            if item.startswith('.'):
                continue
                
            item_path = os.path.join(path, item)
            
            # Check if this path should be excluded
            if should_exclude_path(item_path, repo_folder):
                print(f"Excluding: {os.path.relpath(item_path, repo_folder)}")
                continue
            
            if os.path.isdir(item_path):
                print(f"Processing directory: {os.path.relpath(item_path, repo_folder)}")
                # Create directory element
                dir_element = ET.SubElement(parent_element, "directory")
                dir_element.set("name", item)
                dir_element.set("path", os.path.relpath(item_path, repo_folder))
                
                # Recursively process subdirectory
                build_structure_xml(dir_element, item_path, level + 1)
            else:
                print(f"Processing file: {os.path.relpath(item_path, repo_folder)}")
                # Create file element
                file_element = ET.SubElement(parent_element, "file")
                file_element.set("name", item)
                file_element.set("path", os.path.relpath(item_path, repo_folder))
                
                # Get file extension for language detection
                _, ext = os.path.splitext(item)
                extension_to_language = {
                    '.py': 'python',
                    '.js': 'javascript',
                    '.ts': 'typescript',
                    '.jsx': 'javascript',
                    '.tsx': 'typescript',
                    '.java': 'java',
                    '.cpp': 'cpp',
                    '.c': 'c',
                    '.cs': 'csharp',
                    '.html': 'html',
                    '.css': 'css',
                    '.rb': 'ruby',
                    '.php': 'php',
                    '.go': 'go',
                    '.rs': 'rust',
                    '.swift': 'swift',
                    '.kt': 'kotlin',
                    '.sh': 'bash',
                    '.md': 'markdown',
                    '.json': 'json',
                    '.xml': 'xml',
                    '.yaml': 'yaml',
                    '.yml': 'yaml',
                    '.sql': 'sql',
                    '.r': 'r',
                    '.scala': 'scala',
                }
                
                language = extension_to_language.get(ext.lower(), 'text')
                file_element.set("language", language)
                
                # Try to read file content
                try:
                    # Check file size first
                    file_size = os.path.getsize(item_path)
                    if file_size > 10 * 1024 * 1024:  # Skip files larger than 10MB
                        print(f"Skipping large file ({file_size} bytes): {item_path}")
                        content_element = ET.SubElement(file_element, "content")
                        content_element.text = f"[File too large: {file_size} bytes]"
                        continue
                    
                    with open(item_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Clean content to ensure valid XML
                    # Remove or replace invalid XML characters
                    # Remove control characters except tab, newline, carriage return
                    content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
                    
                    # Add content as text (ElementTree will handle escaping)
                    content_element = ET.SubElement(file_element, "content")
                    content_element.text = content
                    
                except (UnicodeDecodeError, PermissionError, OSError) as e:
                    # Skip binary files or files we can't read
                    print(f"Skipping file (error: {e}): {item_path}")
                    content_element = ET.SubElement(file_element, "content")
                    content_element.text = f"[Binary or unreadable file: {str(e)}]"

    try:
        if not os.path.isdir(repo_folder):
            raise ValueError(f"The provided path '{repo_folder}' is not a valid directory.")

        print(f"Starting processing of: {repo_folder}")
        if exclude_folders:
            print(f"Excluding folders: {', '.join(exclude_folders)}")
        if exclude_files:
            print(f"Excluding files: {', '.join(exclude_files)}")
        
        # Create root XML element
        root = ET.Element("repository")
        root.set("source_path", os.path.abspath(repo_folder))
        root.set("name", os.path.basename(repo_folder))
        if exclude_folders:
            root.set("excluded_folders", ', '.join(exclude_folders))
        if exclude_files:
            root.set("excluded_files", ', '.join(exclude_files))
        
        # Add structure element
        structure_element = ET.SubElement(root, "structure")
        
        # Build the XML structure
        print("Building XML structure...")
        build_structure_xml(structure_element, repo_folder)
        
        # Create the tree and write to file
        print("Writing XML to file...")
        tree = ET.ElementTree(root)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Write XML with pretty formatting
        print("Formatting XML...")
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        # Remove empty lines that minidom adds
        pretty_lines = [line for line in pretty_xml.split('\n') if line.strip()]
        final_xml = '\n'.join(pretty_lines)
        
        print("Saving to file...")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_xml)
        
        print(f"Repository structure and contents saved to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating XML description: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Convert local directory structure and contents to XML format.')
    parser.add_argument('source_path', help='Path to the local directory to process')
    parser.add_argument('-o', '--output', required=True, help='Output XML file path')
    parser.add_argument('--exclude', nargs='*', default=[], help='Folder paths to exclude from processing (e.g., --exclude utils components/ui hooks/__tests__)')
    parser.add_argument('--exclude-files', nargs='*', default=[], help='Specific files to exclude (e.g., --exclude-files "components/reader/file.epub" "components/reader/doc.md")')
    
    args = parser.parse_args()
    
    source_path = os.path.abspath(args.source_path)
    output_path = os.path.abspath(args.output)
    exclude_folders = args.exclude
    exclude_files = args.exclude_files
    
    if not os.path.exists(source_path):
        print(f"Error: Source path '{source_path}' does not exist.")
        return 1
    
    if not os.path.isdir(source_path):
        print(f"Error: Source path '{source_path}' is not a directory.")
        return 1
    
    print(f"Processing directory: {source_path}")
    print(f"Output file: {output_path}")
    if exclude_folders:
        print(f"Excluding folders: {exclude_folders}")
    if exclude_files:
        print(f"Excluding files: {exclude_files}")
    
    try:
        describe_repo_contents_xml(source_path, output_path, exclude_folders, exclude_files)
        print("Successfully completed!")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 

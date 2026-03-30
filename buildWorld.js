export function buildWorld(files) {
  const root = { children: {}, files: [] };

  for (const file of files) {
    const parts = file.path.split("/").filter(Boolean);
    const filename = parts.pop();
    let node = root;

    for (const part of parts) {
      if (!node.children[part]) {
        node.children[part] = { children: {}, files: [] };
      }
      node = node.children[part];
    }

    node.files.push({ name: filename, content: file.content });
  }

  return root;
}

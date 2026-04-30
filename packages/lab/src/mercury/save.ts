import { DocumentRegistry } from '@jupyterlab/docregistry';
import type { INotebookContent } from '@jupyterlab/nbformat';
import { INotebookModel } from '@jupyterlab/notebook';

type NotebookContent = INotebookContent;

const patchedContexts = new WeakSet<
  DocumentRegistry.IContext<INotebookModel>
>();

export function sanitizeMercuryNotebookContent(
  notebook: NotebookContent
): NotebookContent {
  const sanitized = JSON.parse(JSON.stringify(notebook)) as NotebookContent;

  if (sanitized.metadata) {
    delete (sanitized.metadata as Record<string, unknown>).widgets;
  }

  for (const cell of sanitized.cells ?? []) {
    if (cell.cell_type !== 'code') {
      continue;
    }

    cell.outputs = [];
    cell.execution_count = null;
  }

  return sanitized;
}

export function installMercurySaveSanitizer(
  context: DocumentRegistry.IContext<INotebookModel>
): void {
  if (patchedContexts.has(context)) {
    return;
  }

  patchedContexts.add(context);
  const model = context.model;
  const originalSave = context.save.bind(context);

  context.save = (async () => {
    const originalToJSON = model.toJSON.bind(model);

    model.toJSON = (() => {
      return sanitizeMercuryNotebookContent(
        originalToJSON() as NotebookContent
      );
    }) as INotebookModel['toJSON'];

    try {
      await originalSave();
    } finally {
      model.toJSON = originalToJSON as INotebookModel['toJSON'];
    }
  }) as typeof context.save;
}

export async function saveMercuryNotebook(
  context: DocumentRegistry.IContext<INotebookModel>
): Promise<void> {
  installMercurySaveSanitizer(context);
  await context.save();
}

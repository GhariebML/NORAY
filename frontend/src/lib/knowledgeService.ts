"use client";

import { workspaceApi } from "@/lib/api";

export type KnowledgeEventType =
  | "DocumentUploaded"
  | "DocumentIndexed"
  | "KnowledgeUpdated"
  | "DocumentDeleted"
  | "DocumentReindexed";

export interface KnowledgeEvent {
  type: KnowledgeEventType;
  payload?: any;
  timestamp: string;
}

type Listener = (event: KnowledgeEvent) => void;

class KnowledgeEventBus {
  private listeners: Listener[] = [];

  subscribe(listener: Listener): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  publish(type: KnowledgeEventType, payload?: any) {
    const event: KnowledgeEvent = {
      type,
      payload,
      timestamp: new Date().toISOString(),
    };
    this.listeners.forEach((listener) => {
      try {
        listener(event);
      } catch (err) {
        console.error("KnowledgeEventBus listener error:", err);
      }
    });
  }
}

export const knowledgeEventBus = new KnowledgeEventBus();

export interface QueueItem {
  id: string;
  file: File;
  progress: number;
  status: "queued" | "uploading" | "extracting" | "ocr" | "chunking" | "embedding" | "indexing" | "completed" | "failed";
  stage: string;
  category: string;
  logs: string[];
  chunksCount?: number;
  error?: string;
}

export class KnowledgeService {
  private static instance: KnowledgeService;
  private queue: QueueItem[] = [];
  private listeners: ((queue: QueueItem[]) => void)[] = [];

  private constructor() {}

  public static getInstance(): KnowledgeService {
    if (!KnowledgeService.instance) {
      KnowledgeService.instance = new KnowledgeService();
    }
    return KnowledgeService.instance;
  }

  public subscribeQueue(listener: (queue: QueueItem[]) => void): () => void {
    this.listeners.push(listener);
    listener([...this.queue]);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach((l) => l([...this.queue]));
  }

  public async uploadFiles(files: File[], category: string = "general") {
    const newItems: QueueItem[] = files.map((file) => ({
      id: Math.random().toString(36).substring(7),
      file,
      progress: 0,
      status: "queued",
      stage: "Queued",
      category,
      logs: [`[${new Date().toLocaleTimeString()}] Queued file in background ingestion engine.`],
    }));

    this.queue = [...this.queue, ...newItems];
    this.notify();

    for (const item of newItems) {
      this.processItem(item);
    }
  }

  private async processItem(item: QueueItem) {
    const update = (updates: Partial<QueueItem>, logMsg?: string) => {
      this.queue = this.queue.map((q) => {
        if (q.id === item.id) {
          const logs = logMsg ? [...q.logs, `[${new Date().toLocaleTimeString()}] ${logMsg}`] : q.logs;
          return { ...q, ...updates, logs };
        }
        return q;
      });
      this.notify();
    };

    try {
      update({ status: "uploading", stage: "Uploading & ingesting", progress: 20 }, `Uploading ${item.file.name} (${(item.file.size / 1024).toFixed(0)} KB)...`);

      const res = await workspaceApi.uploadDoc(item.file, item.category);

      update(
        {
          status: "completed",
          stage: "Ingested",
          progress: 100,
          chunksCount: res.chunks_count,
        },
        `Ingested ${res.chunks_count} chunks successfully using ${res.strategy} strategy.`
      );

      knowledgeEventBus.publish("DocumentUploaded", { file: item.file.name, category: item.category });
      knowledgeEventBus.publish("KnowledgeUpdated", { source: item.file.name });
    } catch (e: any) {
      const detail = e.message || "Failed processing file";
      update(
        {
          status: "failed",
          stage: "Ingestion failed",
          error: detail,
        },
        `Failure Cause: ${detail}`
      );
    }
  }

  public cancel(id: string) {
    this.queue = this.queue.filter((q) => q.id !== id);
    this.notify();
  }

  public retry(id: string) {
    const item = this.queue.find((q) => q.id === id);
    if (item) {
      item.status = "queued";
      item.progress = 0;
      item.stage = "Queued";
      item.logs = [`[${new Date().toLocaleTimeString()}] Retrying ingestion process.`];
      this.notify();
      this.processItem(item);
    }
  }

  public clearCompleted() {
    this.queue = this.queue.filter((q) => q.status !== "completed");
    this.notify();
  }
}

export const knowledgeService = KnowledgeService.getInstance();

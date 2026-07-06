import axios from 'axios';

interface ErrorPayload {
  detail?: string;
  message?: string;
  code?: string;
  [key: string]: unknown;
}

function defaultMessageForStatus(status: number | null) {
  if (status === 401) {
    return 'Sessao expirada ou acesso nao autorizado.';
  }
  if (status === 403) {
    return 'Voce nao tem permissao para executar esta acao.';
  }
  if (status === 404) {
    return 'Recurso nao encontrado.';
  }
  return 'Erro inesperado na comunicacao com a API.';
}

function extractMessage(payload: ErrorPayload | undefined, status: number | null, fallback: string) {
  if (typeof payload?.detail === 'string' && payload.detail.trim()) {
    return payload.detail;
  }
  if (typeof payload?.message === 'string' && payload.message.trim()) {
    return payload.message;
  }
  return fallback || defaultMessageForStatus(status);
}

export class AppHttpError extends Error {
  status: number | null;
  code: string | null;
  details: unknown;
  originalError: unknown;

  constructor(
    message: string,
    options?: {
      status?: number | null;
      code?: string | null;
      details?: unknown;
      originalError?: unknown;
    }
  ) {
    super(message);
    this.name = 'AppHttpError';
    this.status = options?.status ?? null;
    this.code = options?.code ?? null;
    this.details = options?.details;
    this.originalError = options?.originalError;
  }
}

export function toAppHttpError(error: unknown) {
  if (error instanceof AppHttpError) {
    return error;
  }

  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? null;
    const payload = error.response?.data as ErrorPayload | undefined;

    return new AppHttpError(
      extractMessage(payload, status, error.message),
      {
        status,
        code: typeof payload?.code === 'string' ? payload.code : null,
        details: payload,
        originalError: error,
      }
    );
  }

  if (error instanceof Error) {
    return new AppHttpError(error.message, { originalError: error });
  }

  return new AppHttpError('Erro inesperado na aplicacao.', { originalError: error });
}

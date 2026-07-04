import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Settings } from '../../api/settings';

const documentsSchema = z.object({
  pdf_header_text: z.string().optional(),
  pdf_footer_text: z.string().optional(),
  default_proposal_message: z.string().optional(),
});

type DocumentsFormData = z.infer<typeof documentsSchema>;

interface DocumentsSettingsFormProps {
  settings: Settings;
  onSave: (data: Partial<Settings>) => void;
  isSaving: boolean;
  canEdit: boolean;
}

export function DocumentsSettingsForm({ settings, onSave, isSaving, canEdit }: DocumentsSettingsFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DocumentsFormData>({
    resolver: zodResolver(documentsSchema),
    defaultValues: {
      pdf_header_text: settings.pdf_header_text || '',
      pdf_footer_text: settings.pdf_footer_text || '',
      default_proposal_message: settings.default_proposal_message || '',
    },
  });

  const onSubmit = (data: DocumentsFormData) => {
    onSave(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-6">
        {/* Cabeçalho PDF */}
        <div>
          <label htmlFor="pdf_header_text" className="block text-sm font-medium text-gray-700 mb-1">
            Texto Padrão de Cabeçalho (PDF)
          </label>
          <textarea
            id="pdf_header_text"
            {...register('pdf_header_text')}
            disabled={!canEdit}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed font-mono text-sm"
            placeholder="Ex: EMPRESA XYZ LTDA - CNPJ 00.000.000/0001-00&#10;Rua Exemplo, 123 - São Paulo/SP&#10;Tel: (11) 3333-4444"
          />
          {errors.pdf_header_text && <p className="mt-1 text-sm text-red-600">{errors.pdf_header_text.message}</p>}
          <p className="mt-2 text-xs text-gray-500">
            Este texto aparecerá no cabeçalho de propostas, ordens de serviço e relatórios em PDF.
          </p>
        </div>

        {/* Rodapé PDF */}
        <div>
          <label htmlFor="pdf_footer_text" className="block text-sm font-medium text-gray-700 mb-1">
            Texto Padrão de Rodapé (PDF)
          </label>
          <textarea
            id="pdf_footer_text"
            {...register('pdf_footer_text')}
            disabled={!canEdit}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed font-mono text-sm"
            placeholder="Ex: Documento gerado eletronicamente - www.empresa.com.br"
          />
          {errors.pdf_footer_text && <p className="mt-1 text-sm text-red-600">{errors.pdf_footer_text.message}</p>}
          <p className="mt-2 text-xs text-gray-500">
            Este texto aparecerá no rodapé de todos os documentos PDF gerados pelo sistema.
          </p>
        </div>

        {/* Mensagem Padrão Proposta */}
        <div>
          <label htmlFor="default_proposal_message" className="block text-sm font-medium text-gray-700 mb-1">
            Mensagem Padrão de Proposta/OS
          </label>
          <textarea
            id="default_proposal_message"
            {...register('default_proposal_message')}
            disabled={!canEdit}
            rows={8}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="Ex:&#10;Prezado Cliente,&#10;&#10;Segue nossa proposta comercial para os serviços solicitados.&#10;&#10;Estamos à disposição para esclarecimentos.&#10;&#10;Atenciosamente,&#10;Equipe Comercial"
          />
          {errors.default_proposal_message && <p className="mt-1 text-sm text-red-600">{errors.default_proposal_message.message}</p>}
          <p className="mt-2 text-xs text-gray-500">
            Esta mensagem será pré-preenchida automaticamente ao criar novas propostas e ordens de serviço.
            Você poderá editá-la caso a caso.
          </p>
        </div>
      </div>

      {/* Dica */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-amber-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <h4 className="text-sm font-medium text-amber-900">
              💡 Dica de Uso
            </h4>
            <p className="mt-1 text-sm text-amber-700">
              Configure estes textos uma vez e economize tempo ao gerar documentos.
              Você pode usar variáveis como {'{'}empresa{'}'}, {'{'}cnpj{'}'}, {'{'}data{'}'} que serão substituídas automaticamente na geração do PDF.
            </p>
          </div>
        </div>
      </div>

      {/* Preview Box */}
      <div className="bg-white border-2 border-gray-300 rounded-lg p-6 shadow-sm">
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          📄 Preview de Documento
        </h4>
        <div className="space-y-4 text-sm">
          <div className="border-b border-gray-200 pb-3">
            <p className="text-xs text-gray-400 mb-1">CABEÇALHO</p>
            <p className="whitespace-pre-line text-gray-700 font-mono text-xs">
              {register('pdf_header_text').name ? 'Seu texto de cabeçalho...' : <span className="text-gray-400 italic">Nenhum cabeçalho definido</span>}
            </p>
          </div>
          <div className="py-3 text-center text-gray-400 italic text-xs">
            [Conteúdo do documento]
          </div>
          <div className="border-t border-gray-200 pt-3">
            <p className="text-xs text-gray-400 mb-1">RODAPÉ</p>
            <p className="whitespace-pre-line text-gray-700 font-mono text-xs">
              {register('pdf_footer_text').name ? 'Seu texto de rodapé...' : <span className="text-gray-400 italic">Nenhum rodapé definido</span>}
            </p>
          </div>
        </div>
      </div>

      {/* Botão Salvar */}
      {canEdit && (
        <div className="flex justify-end pt-4 border-t border-gray-200">
          <button
            type="submit"
            disabled={isSaving}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
      )}
    </form>
  );
}

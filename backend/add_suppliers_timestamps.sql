-- Adiciona campos created_at e updated_at na tabela suppliers se não existirem

DO $$
BEGIN
    -- Adicionar created_at se não existir
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'suppliers' 
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE core.suppliers 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL;
        
        RAISE NOTICE '✅ Campo created_at criado';
    ELSE
        RAISE NOTICE '✓ Campo created_at já existe';
    END IF;
    
    -- Adicionar updated_at se não existir
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'suppliers' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE core.suppliers 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL;
        
        -- Trigger para atualizar updated_at automaticamente
        CREATE OR REPLACE FUNCTION core.update_suppliers_updated_at()
        RETURNS TRIGGER AS $func$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $func$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trg_suppliers_updated_at
        BEFORE UPDATE ON core.suppliers
        FOR EACH ROW
        EXECUTE FUNCTION core.update_suppliers_updated_at();
        
        RAISE NOTICE '✅ Campo updated_at criado com trigger';
    ELSE
        RAISE NOTICE '✓ Campo updated_at já existe';
    END IF;
END $$;

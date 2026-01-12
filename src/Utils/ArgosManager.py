import argostranslate.package
import logging

class ArgosManager:
    @staticmethod
    def garantir_pacote_instalado(from_code: str, to_code: str):
        """
        Verifica se o pacote de tradução está instalado, caso contrário, realiza o download.
        """
        logger = logging.getLogger("ArgosManager")
        logger.info(f"Verificando pacote de tradução: {from_code} -> {to_code}")

        try:
            # 1. Atualiza o índice (necessário para downloads)
            argostranslate.package.update_package_index()
            
            # 2. Verifica se já está instalado para evitar download desnecessário
            installed_packages = argostranslate.package.get_installed_packages()
            is_installed = any(
                p.from_code == from_code and p.to_code == to_code 
                for p in installed_packages
            )

            if is_installed:
                logger.info(f"Pacote {from_code}->{to_code} já está pronto para uso.")
                return True

            # 3. Busca o pacote nos disponíveis
            available_packages = argostranslate.package.get_available_packages()
            package_to_install = next(
                filter(
                    lambda x: x.from_code == from_code and x.to_code == to_code, 
                    available_packages
                ), None
            )

            if package_to_install:
                logger.info(f"Baixando e instalando pacote {from_code}->{to_code} (isso pode demorar)...")
                argostranslate.package.install_from_path(package_to_install.download())
                logger.info("Instalação concluída com sucesso.")
                return True
            else:
                logger.error(f"Pacote de tradução {from_code}->{to_code} não disponível no índice.")
                return False

        except Exception as e:
            logger.error(f"Erro ao gerenciar pacotes Argos: {e}")
            return False
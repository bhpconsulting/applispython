# -*- coding: utf-8 -*-
"""
Adapté le 24 Décembre 2024 pour recherche approximative et surlignage des mots-clés
"""
def run():
    import requests
    from io import BytesIO
    import fitz  # PyMuPDF pour la manipulation des fichiers PDF
    from fuzzysearch import find_near_matches  # Recherche approximative
    import unicodedata
    import streamlit as st
    import base64
    
    #--------------------------------
    def tri_result(results):
        # tri de 'results' par ordre décroissant d'occurrence des mots-clés 
        results_new = []
        for result in results:
            st.write("result",result)

            nb_occur = 0 # nombre d'occurrences d'un ou des mots-clé(s) dans le fichier
            for keyword, positions in result['matches'].items():
                # positions est une liste de tuples. Un tuple = (start,end) du mot-clé
                nb_occur += len(positions)
            # s'il y a au moins une occurrence on crée un élément (dictionnaire) dans la liste 'results_new'  
            # en rajoutant un élément du dictionnaire (nb_occur)
            if nb_occur != 0: 
                url = result['url']
                matches = result['matches']
                nom = result['nom']
                results_new.append({"url": url, "matches": matches,"nom": nom,"nb_occur": nb_occur})
    
        # la liste results_sorted est trié sur la clé 'nb_occur'
        results_sorted = sorted(results_new, key=lambda x: x["nb_occur"], reverse = True)
        return results_sorted  

    #-------------------------------
    def normaliser_texte(texte):
        # Transforme les caractères accentués en leur équivalent sans accent
        texte = unicodedata.normalize('NFD', texte)
        texte = ''.join(c for c in texte if unicodedata.category(c) != 'Mn')
        # Conversion en minuscules
        texte = texte.lower()
        return texte

    # --------------------------------
    def extract_text_fitz(pdf_file):
        # Lit le fichier PDF et extrait le texte avec PyMuPDF
        with fitz.open(stream=pdf_file, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        return text

    #---------------------------------------
    def recherche_keywords_approximatif(text, keywords, max_dist):
        # Supprime les accents du texte et des mots-clés
        text_normalise = normaliser_texte(text)
        keywords_normalises = [normaliser_texte(keyword) for keyword in keywords]

        results = {}
        for original, normalise in zip(keywords, keywords_normalises):
            matches = find_near_matches(normalise, text_normalise, max_l_dist=max_dist)
            results[original] = [(m.start, m.end) for m in matches]
        return results

    #----------------------------------
    def surligner_mots_cles(pdf_file, mots_cles_positions, output_path):
        with fitz.open(stream=pdf_file, filetype="pdf") as doc:
            for page_num, positions in mots_cles_positions.items():
                page = doc[page_num]
                for (start, end) in positions:
                    try:
                        # Extrait le texte correspondant
                        text_segment = page.get_text()[start:end]
                     
                        # Recherche dans la page
                        rects = page.search_for(text_segment)

                        if rects:
                            for rect in rects:
                                page.add_highlight_annot(rect)
                        else:
                            st.write(f"Aucune correspondance exacte pour '{text_segment}' à la page {page_num}.")
                    except Exception as e:
                        st.write(f"Erreur surlignage pour '{text_segment}' à la page {page_num} : {e}")

            # Sauvegarde le fichier PDF avec les surlignages
            doc.save(output_path)

    #----------------------------------
    def recherche_et_surligne_pdf(nom, url, keywords, output_path, max_dist):
        # Extraction du texte, recherche des mots-clés et surlignage dans le PDF
        try:
            response = requests.get(url)  # Téléchargement du fichier
            response.raise_for_status()

            with BytesIO(response.content) as pdf_file:
                # Extraction du texte
                text = extract_text_fitz(pdf_file)
                
                # Recherche approximative des mots-clés
                keyword_matches = recherche_keywords_approximatif(text, keywords, max_dist)
                
                # Association des positions trouvées avec les numéros de pages
                mots_cles_positions = {}
                with fitz.open(stream=pdf_file, filetype="pdf") as doc:
                    for page_num, page in enumerate(doc):
                        page_text = page.get_text()
                        mots_cles_positions[page_num] = [
                            (m.start, m.end) for keyword in keywords 
                            for m in find_near_matches(normaliser_texte(keyword), normaliser_texte(page_text), max_l_dist=max_dist)
                          ]

                succes = False  # succes = True s'il y a au moins un mot-clé trouvé
                for page_num, positions in mots_cles_positions.items():
                    if positions != []:
                        succes = True
                        break
                    
                if succes: # on ne surligne que s'il y a au moins un mot-clé trouvé
                    # surlignage des mots-clés
                    surligner_mots_cles(response.content, mots_cles_positions, output_path)
                
                    return {"url": url, "matches": keyword_matches, "nom": nom}
                else:
                    return {}
                
        except requests.RequestException as e:
            return {"error": f"Erreur téléchargement {url}: {e}"}
        except Exception as e:
            return {"error": f"Erreur lecture/surlignage PDF {url}: {e}"}

    #----------------------------------
    keywords = "AGIRabcd"
    keywords = keywords.split(',')  # Transformation de la chaîne en liste
    nom = "NWL90"
    url = "https://www.agirabcd.fr/NEWSLETTER/N90/N90_NWL.pdf"
    output_path = "resultat_surligne.pdf"
    max_dist = 1

    results = recherche_et_surligne_pdf(nom, url, keywords, output_path, max_dist)
    st.write(results)
    
    # tri de 'results' par ordre d'occurrence des mots-clés décroissant
    #results_sorted = tri_result(results)

    # Lire le fichier PDF
    with open(output_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    # Convertir les données PDF en base64
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    
    st.download_button(
        label="Télécharger le PDF",
        data=pdf_bytes,
        file_name=output_path,
        mime="application/pdf"
    )

    # Afficher le PDF dans une iframe
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="500" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
    
# Si l'application est lancée directement (en dehors du portail), lancer l'application
if __name__ == "__main__":    
    run()    

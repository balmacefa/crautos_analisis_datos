# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: search.spec.js >> Search Explorer Enhancements >> should update price range options when switching currency
- Location: tests\search.spec.js:57:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator:  locator('select').filter({ hasText: 'Min' }).first().locator('option[value="2000000"]')
Expected: visible
Received: hidden
Timeout:  5000ms

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('select').filter({ hasText: 'Min' }).first().locator('option[value="2000000"]')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - main [ref=e2]:
    - generic:
      - img
    - generic [ref=e4]:
      - generic [ref=e5]:
        - link [ref=e6] [cursor=pointer]:
          - /url: /
          - img [ref=e7]
        - generic [ref=e9]:
          - heading "Crautos Search" [level=2] [ref=e10]
          - paragraph [ref=e11]: Market Explorer v2
      - generic [ref=e12]:
        - img [ref=e13]
        - textbox "Marca, modelo, año, provincia o precio..." [ref=e16]
      - button "Filtros" [ref=e18]:
        - img [ref=e19]
        - text: Filtros
    - generic [ref=e21]:
      - complementary [ref=e22]:
        - generic [ref=e23]:
          - heading "Parámetros" [level=3] [ref=e24]:
            - img [ref=e25]
            - text: Parámetros
          - generic [ref=e28]:
            - generic [ref=e29]:
              - generic [ref=e30]:
                - generic [ref=e31]: Vehículo
                - generic [ref=e32]:
                  - button [ref=e33]:
                    - img [ref=e34]
                  - button [ref=e36]:
                    - img [ref=e37]
              - generic [ref=e38]:
                - button "TOYOTA" [ref=e39]
                - button "HYUNDAI" [ref=e40]
                - button "NISSAN" [ref=e41]
                - button "SUZUKI" [ref=e42]
                - button "KIA" [ref=e43]
                - button "MITSUBISHI" [ref=e44]
                - button "BMW" [ref=e45]
                - button "HONDA" [ref=e46]
                - button "CHEVROLET" [ref=e47]
                - button "FORD" [ref=e48]
            - generic [ref=e49]:
              - generic [ref=e50]:
                - generic [ref=e51]: Rango de Precio (CRC)
                - generic [ref=e52]:
                  - button "CRC" [ref=e53]
                  - button "USD" [ref=e54]
              - generic [ref=e55]:
                - generic [ref=e56]:
                  - combobox [ref=e57]:
                    - option "Min" [selected]
                    - option "₡2M"
                    - option "₡5M"
                    - option "₡10M"
                    - option "₡15M"
                    - option "₡20M"
                    - option "₡30M"
                  - img
                - generic [ref=e58]:
                  - combobox [ref=e59]:
                    - option "Max" [selected]
                    - option "₡5M"
                    - option "₡10M"
                    - option "₡15M"
                    - option "₡20M"
                    - option "₡30M"
                    - option "₡50M"
                  - img
            - generic [ref=e60]:
              - text: Años
              - generic [ref=e61]:
                - combobox [ref=e62]:
                  - option "Todos los años" [selected]
                  - option "2024 (605)"
                  - option "2023 (703)"
                  - option "2022 (598)"
                  - option "2019 (597)"
                  - option "2018 (849)"
                  - option "2017 (1218)"
                  - option "2016 (914)"
                  - option "2015 (651)"
                  - option "2014 (654)"
                  - option "2013 (628)"
                - img
            - generic [ref=e63]:
              - text: Provincia
              - generic [ref=e64]:
                - combobox [ref=e65]:
                  - option "Todas las provincias" [selected]
                  - option "San José"
                  - option "Heredia"
                  - option "Alajuela"
                  - option "Cartago"
                  - option "Guanacaste"
                  - option "Puntarenas"
                  - option "Limón"
                - img
            - generic [ref=e66]:
              - text: Combustible
              - generic [ref=e67]:
                - button "Gasolina" [ref=e68]
                - button "Diesel" [ref=e69]
                - button "Eléctrico" [ref=e70]
                - button "Híbrido" [ref=e71]
            - generic [ref=e72]:
              - text: Ordenar por
              - generic [ref=e73]:
                - combobox [ref=e74]:
                  - option "Más Recientes" [selected]
                  - option "Menor Precio"
                  - option "Mayor Precio"
                  - option "Menor Kilometraje"
                - img
            - generic [ref=e75]:
              - text: Fuente de Datos
              - button "CRAutos 12674" [ref=e77]:
                - generic [ref=e78]: CRAutos
                - generic [ref=e79]: "12674"
        - generic [ref=e80]:
          - generic [ref=e81]:
            - img [ref=e82]
            - text: Sugerencia IA
          - paragraph [ref=e85]: "\"Recuerda que los autos con menos de 80,000km suelen tener mejor valor de reventa en Costa Rica.\""
      - generic [ref=e86]:
        - generic [ref=e88]:
          - heading "Explora el Mercado" [level=1] [ref=e89]
          - paragraph [ref=e90]: Mostrando 20 de 12,674 anuncios activos
        - generic [ref=e91]:
          - generic [ref=e92] [cursor=pointer]:
            - button [ref=e93]:
              - img [ref=e94]
            - generic [ref=e96]:
              - img "FOTON TUNLAND V9" [ref=e97]
              - generic [ref=e98]: "2026"
            - generic [ref=e99]:
              - generic [ref=e100]:
                - heading "FOTON" [level=3] [ref=e101]
                - paragraph [ref=e102]: TUNLAND V9
              - generic [ref=e103]:
                - generic [ref=e104]:
                  - img [ref=e105]
                  - generic [ref=e108]: 13,800 KM
                - generic [ref=e109]:
                  - img [ref=e110]
                  - generic [ref=e113]: San José
              - generic [ref=e114]:
                - generic [ref=e115]:
                  - paragraph [ref=e116]: Precio
                  - generic [ref=e117]:
                    - generic [ref=e118]: ₡38,900
                    - generic [ref=e119]: $18,944,300
                - img [ref=e121]
          - generic [ref=e123] [cursor=pointer]:
            - button [ref=e124]:
              - img [ref=e125]
            - generic [ref=e127]:
              - img "TOYOTA LAND CRUISER" [ref=e128]
              - generic [ref=e129]: "2026"
            - generic [ref=e130]:
              - generic [ref=e131]:
                - heading "TOYOTA" [level=3] [ref=e132]
                - paragraph [ref=e133]: LAND CRUISER
              - generic [ref=e134]:
                - generic [ref=e135]:
                  - img [ref=e136]
                  - generic [ref=e139]: 22 KM
                - generic [ref=e140]:
                  - img [ref=e141]
                  - generic [ref=e144]: Cartago
              - generic [ref=e145]:
                - generic [ref=e146]:
                  - paragraph [ref=e147]: Precio
                  - generic [ref=e148]:
                    - generic [ref=e149]: ₡55,150,000
                    - generic [ref=e150]: $113,244
                - img [ref=e152]
          - generic [ref=e154] [cursor=pointer]:
            - button [ref=e155]:
              - img [ref=e156]
            - generic [ref=e158]:
              - img [ref=e159]
              - generic [ref=e163]: "2026"
            - generic [ref=e164]:
              - generic [ref=e165]:
                - heading "BMW" [level=3] [ref=e166]
                - paragraph [ref=e167]: IX1 PAQUETE M
              - generic [ref=e168]:
                - generic [ref=e169]:
                  - img [ref=e170]
                  - generic [ref=e173]: 50 KM
                - generic [ref=e174]:
                  - img [ref=e175]
                  - generic [ref=e178]: San José
              - generic [ref=e179]:
                - generic [ref=e180]:
                  - paragraph [ref=e181]: Precio
                  - generic [ref=e182]:
                    - generic [ref=e183]: ₡27,000,000
                    - generic [ref=e184]: $55,441
                - img [ref=e186]
          - generic [ref=e188] [cursor=pointer]:
            - button [ref=e189]:
              - img [ref=e190]
            - generic [ref=e192]:
              - img "CHERY TIGGO 2 PRO MAX" [ref=e193]
              - generic [ref=e194]: "2026"
            - generic [ref=e195]:
              - generic [ref=e196]:
                - heading "CHERY" [level=3] [ref=e197]
                - paragraph [ref=e198]: TIGGO 2 PRO MAX
              - generic [ref=e199]:
                - generic [ref=e200]:
                  - img [ref=e201]
                  - generic [ref=e204]: 15,000 KM
                - generic [ref=e205]:
                  - img [ref=e206]
                  - generic [ref=e209]: Cartago
              - generic [ref=e210]:
                - generic [ref=e211]:
                  - paragraph [ref=e212]: Precio
                  - generic [ref=e213]:
                    - generic [ref=e214]: ₡7,500,000
                    - generic [ref=e215]: $15,400
                - img [ref=e217]
          - generic [ref=e219] [cursor=pointer]:
            - button [ref=e220]:
              - img [ref=e221]
            - generic [ref=e223]:
              - img "TOYOTA LITEACE" [ref=e224]
              - generic [ref=e225]: "2026"
            - generic [ref=e226]:
              - generic [ref=e227]:
                - heading "TOYOTA" [level=3] [ref=e228]
                - paragraph [ref=e229]: LITEACE
              - generic [ref=e230]:
                - generic [ref=e231]:
                  - img [ref=e232]
                  - generic [ref=e235]: 1,875 KM
                - generic [ref=e236]:
                  - img [ref=e237]
                  - generic [ref=e240]: Heredia
              - generic [ref=e241]:
                - generic [ref=e242]:
                  - paragraph [ref=e243]: Precio
                  - generic [ref=e244]:
                    - generic [ref=e245]: ₡12,000,000
                    - generic [ref=e246]: $24,641
                - img [ref=e248]
          - generic [ref=e250] [cursor=pointer]:
            - button [ref=e251]:
              - img [ref=e252]
            - generic [ref=e254]:
              - img "DODGE/RAM 1500 BIG HORN" [ref=e255]
              - generic [ref=e256]: "2026"
            - generic [ref=e257]:
              - generic [ref=e258]:
                - heading "DODGE/RAM" [level=3] [ref=e259]
                - paragraph [ref=e260]: 1500 BIG HORN
              - generic [ref=e261]:
                - generic [ref=e262]:
                  - img [ref=e263]
                  - generic [ref=e266]: 3,000 KM
                - generic [ref=e267]:
                  - img [ref=e268]
                  - generic [ref=e271]: San José
              - generic [ref=e272]:
                - generic [ref=e273]:
                  - paragraph [ref=e274]: Precio
                  - generic [ref=e275]:
                    - generic [ref=e276]: ₡95,000
                    - generic [ref=e277]: $46,265,000
                - img [ref=e279]
          - generic [ref=e281] [cursor=pointer]:
            - button [ref=e282]:
              - img [ref=e283]
            - generic [ref=e285]:
              - img [ref=e286]
              - generic [ref=e290]: "2026"
            - generic [ref=e291]:
              - generic [ref=e292]:
                - heading "HYUNDAI" [level=3] [ref=e293]
                - paragraph [ref=e294]: TUCSON
              - generic [ref=e295]:
                - generic [ref=e296]:
                  - img [ref=e297]
                  - generic [ref=e300]: 15,000 KM
                - generic [ref=e301]:
                  - img [ref=e302]
                  - generic [ref=e305]: San José
              - generic [ref=e306]:
                - generic [ref=e307]:
                  - paragraph [ref=e308]: Precio
                  - generic [ref=e309]:
                    - generic [ref=e310]: ₡18,000,000
                    - generic [ref=e311]: $36,961
                - img [ref=e313]
          - generic [ref=e315] [cursor=pointer]:
            - button [ref=e316]:
              - img [ref=e317]
            - generic [ref=e319]:
              - img "TOYOTA HILUX" [ref=e320]
              - generic [ref=e321]: "2026"
            - generic [ref=e322]:
              - generic [ref=e323]:
                - heading "TOYOTA" [level=3] [ref=e324]
                - paragraph [ref=e325]: HILUX
              - generic [ref=e326]:
                - generic [ref=e327]:
                  - img [ref=e328]
                  - generic [ref=e331]: 0 KM
                - generic [ref=e332]:
                  - img [ref=e333]
                  - generic [ref=e336]: San José
              - generic [ref=e337]:
                - generic [ref=e338]:
                  - paragraph [ref=e339]: Precio
                  - generic [ref=e340]:
                    - generic [ref=e341]: ₡34,950,000
                    - generic [ref=e342]: $71,766
                - img [ref=e344]
          - generic [ref=e346] [cursor=pointer]:
            - button [ref=e347]:
              - img [ref=e348]
            - generic [ref=e350]:
              - img "TOYOTA FORTUNER SRV" [ref=e351]
              - generic [ref=e352]: "2026"
            - generic [ref=e353]:
              - generic [ref=e354]:
                - heading "TOYOTA" [level=3] [ref=e355]
                - paragraph [ref=e356]: FORTUNER SRV
              - generic [ref=e357]:
                - generic [ref=e358]:
                  - img [ref=e359]
                  - generic [ref=e362]: 0 KM
                - generic [ref=e363]:
                  - img [ref=e364]
                  - generic [ref=e367]: San José
              - generic [ref=e368]:
                - generic [ref=e369]:
                  - paragraph [ref=e370]: Precio
                  - generic [ref=e371]:
                    - generic [ref=e372]: ₡33,950,000
                    - generic [ref=e373]: $69,713
                - img [ref=e375]
          - generic [ref=e377] [cursor=pointer]:
            - button [ref=e378]:
              - img [ref=e379]
            - generic [ref=e381]:
              - img "BMW IX1" [ref=e382]
              - generic [ref=e383]: "2026"
            - generic [ref=e384]:
              - generic [ref=e385]:
                - heading "BMW" [level=3] [ref=e386]
                - paragraph [ref=e387]: IX1
              - generic [ref=e388]:
                - generic [ref=e389]:
                  - img [ref=e390]
                  - generic [ref=e393]: 50 KM
                - generic [ref=e394]:
                  - img [ref=e395]
                  - generic [ref=e398]: San José
              - generic [ref=e399]:
                - generic [ref=e400]:
                  - paragraph [ref=e401]: Precio
                  - generic [ref=e402]:
                    - generic [ref=e403]: ₡22,500,000
                    - generic [ref=e404]: $46,201
                - img [ref=e406]
          - generic [ref=e408] [cursor=pointer]:
            - button [ref=e409]:
              - img [ref=e410]
            - generic [ref=e412]:
              - img "MERCEDES BENZ GLE300D COUPE" [ref=e413]
              - generic [ref=e414]: "2026"
            - generic [ref=e415]:
              - generic [ref=e416]:
                - heading "MERCEDES BENZ" [level=3] [ref=e417]
                - paragraph [ref=e418]: GLE300D COUPE
              - generic [ref=e419]:
                - generic [ref=e420]:
                  - img [ref=e421]
                  - generic [ref=e424]: 2,180 KM
                - generic [ref=e425]:
                  - img [ref=e426]
                  - generic [ref=e429]: San José
              - generic [ref=e430]:
                - generic [ref=e431]:
                  - paragraph [ref=e432]: Precio
                  - generic [ref=e433]:
                    - generic [ref=e434]: ₡129,900
                    - generic [ref=e435]: $63,261,300
                - img [ref=e437]
          - generic [ref=e439] [cursor=pointer]:
            - button [ref=e440]:
              - img [ref=e441]
            - generic [ref=e443]:
              - img "MITSUBISHI ECLIPSE CROSS GLS" [ref=e444]
              - generic [ref=e445]: "2026"
            - generic [ref=e446]:
              - generic [ref=e447]:
                - heading "MITSUBISHI" [level=3] [ref=e448]
                - paragraph [ref=e449]: ECLIPSE CROSS GLS
              - generic [ref=e450]:
                - generic [ref=e451]:
                  - img [ref=e452]
                  - generic [ref=e455]: 5,200 KM
                - generic [ref=e456]:
                  - img [ref=e457]
                  - generic [ref=e460]: Heredia
              - generic [ref=e461]:
                - generic [ref=e462]:
                  - paragraph [ref=e463]: Precio
                  - generic [ref=e464]:
                    - generic [ref=e465]: ₡15,500,000
                    - generic [ref=e466]: $31,828
                - img [ref=e468]
          - generic [ref=e470] [cursor=pointer]:
            - button [ref=e471]:
              - img [ref=e472]
            - generic [ref=e474]:
              - img "MITSUBISHI OUTLANDER GLS NEW LINE" [ref=e475]
              - generic [ref=e476]: "2026"
            - generic [ref=e477]:
              - generic [ref=e478]:
                - heading "MITSUBISHI" [level=3] [ref=e479]
                - paragraph [ref=e480]: OUTLANDER GLS NEW LINE
              - generic [ref=e481]:
                - generic [ref=e482]:
                  - img [ref=e483]
                  - generic [ref=e486]: 2,150 KM
                - generic [ref=e487]:
                  - img [ref=e488]
                  - generic [ref=e491]: Heredia
              - generic [ref=e492]:
                - generic [ref=e493]:
                  - paragraph [ref=e494]: Precio
                  - generic [ref=e495]:
                    - generic [ref=e496]: ₡35,900
                    - generic [ref=e497]: $17,483,300
                - img [ref=e499]
          - generic [ref=e501] [cursor=pointer]:
            - button [ref=e502]:
              - img [ref=e503]
            - generic [ref=e505]:
              - img "LAND ROVER DEFENDER DYNAMIC" [ref=e506]
              - generic [ref=e507]: "2026"
            - generic [ref=e508]:
              - generic [ref=e509]:
                - heading "LAND ROVER" [level=3] [ref=e510]
                - paragraph [ref=e511]: DEFENDER DYNAMIC
              - generic [ref=e512]:
                - generic [ref=e513]:
                  - img [ref=e514]
                  - generic [ref=e517]: 0 KM
                - generic [ref=e518]:
                  - img [ref=e519]
                  - generic [ref=e522]: San José
              - generic [ref=e523]:
                - generic [ref=e524]:
                  - paragraph [ref=e525]: Precio
                  - generic [ref=e526]:
                    - generic [ref=e527]: ₡74,950,000
                    - generic [ref=e528]: $153,901
                - img [ref=e530]
          - generic [ref=e532] [cursor=pointer]:
            - button [ref=e533]:
              - img [ref=e534]
            - generic [ref=e536]:
              - img "GEELY GX3 PRO GT" [ref=e537]
              - generic [ref=e538]: "2026"
            - generic [ref=e539]:
              - generic [ref=e540]:
                - heading "GEELY" [level=3] [ref=e541]
                - paragraph [ref=e542]: GX3 PRO GT
              - generic [ref=e543]:
                - generic [ref=e544]:
                  - img [ref=e545]
                  - generic [ref=e548]: 0 KM
                - generic [ref=e549]:
                  - img [ref=e550]
                  - generic [ref=e553]: Alajuela
              - generic [ref=e554]:
                - generic [ref=e555]:
                  - paragraph [ref=e556]: Precio
                  - generic [ref=e557]:
                    - generic [ref=e558]: ₡8,500,000
                    - generic [ref=e559]: $17,454
                - img [ref=e561]
          - generic [ref=e563] [cursor=pointer]:
            - button [ref=e564]:
              - img [ref=e565]
            - generic [ref=e567]:
              - img [ref=e568]
              - generic [ref=e572]: "2026"
            - generic [ref=e573]:
              - generic [ref=e574]:
                - heading "BMW" [level=3] [ref=e575]
                - paragraph [ref=e576]: IX1
              - generic [ref=e577]:
                - generic [ref=e578]:
                  - img [ref=e579]
                  - generic [ref=e582]: 50 KM
                - generic [ref=e583]:
                  - img [ref=e584]
                  - generic [ref=e587]: San José
              - generic [ref=e588]:
                - generic [ref=e589]:
                  - paragraph [ref=e590]: Precio
                  - generic [ref=e591]:
                    - generic [ref=e592]: ₡25,000,000
                    - generic [ref=e593]: $51,335
                - img [ref=e595]
          - generic [ref=e597] [cursor=pointer]:
            - button [ref=e598]:
              - img [ref=e599]
            - generic [ref=e601]:
              - img "TOYOTA LAND CRUISER" [ref=e602]
              - generic [ref=e603]: "2026"
            - generic [ref=e604]:
              - generic [ref=e605]:
                - heading "TOYOTA" [level=3] [ref=e606]
                - paragraph [ref=e607]: LAND CRUISER
              - generic [ref=e608]:
                - generic [ref=e609]:
                  - img [ref=e610]
                  - generic [ref=e613]: 200 KM
                - generic [ref=e614]:
                  - img [ref=e615]
                  - generic [ref=e618]: Alajuela
              - generic [ref=e619]:
                - generic [ref=e620]:
                  - paragraph [ref=e621]: Precio
                  - generic [ref=e622]:
                    - generic [ref=e623]: ₡84,000,000
                    - generic [ref=e624]: $172,485
                - img [ref=e626]
          - generic [ref=e628] [cursor=pointer]:
            - button [ref=e629]:
              - img [ref=e630]
            - generic [ref=e632]:
              - img "KIA K2500" [ref=e633]
              - generic [ref=e634]: "2026"
            - generic [ref=e635]:
              - generic [ref=e636]:
                - heading "KIA" [level=3] [ref=e637]
                - paragraph [ref=e638]: K2500
              - generic [ref=e639]:
                - generic [ref=e640]:
                  - img [ref=e641]
                  - generic [ref=e644]: 100 KM
                - generic [ref=e645]:
                  - img [ref=e646]
                  - generic [ref=e649]: San José
              - generic [ref=e650]:
                - generic [ref=e651]:
                  - paragraph [ref=e652]: Precio
                  - generic [ref=e653]:
                    - generic [ref=e654]: ₡15,900,000
                    - generic [ref=e655]: $32,649
                - img [ref=e657]
          - generic [ref=e659] [cursor=pointer]:
            - button [ref=e660]:
              - img [ref=e661]
            - generic [ref=e663]:
              - img "NISSAN FRONTIER" [ref=e664]
              - generic [ref=e665]: "2026"
            - generic [ref=e666]:
              - generic [ref=e667]:
                - heading "NISSAN" [level=3] [ref=e668]
                - paragraph [ref=e669]: FRONTIER
              - generic [ref=e670]:
                - generic [ref=e671]:
                  - img [ref=e672]
                  - generic [ref=e675]: 0 KM
                - generic [ref=e676]:
                  - img [ref=e677]
                  - generic [ref=e680]: San José
              - generic [ref=e681]:
                - generic [ref=e682]:
                  - paragraph [ref=e683]: Precio
                  - generic [ref=e684]:
                    - generic [ref=e685]: ₡23,950,000
                    - generic [ref=e686]: $49,179
                - img [ref=e688]
          - generic [ref=e690] [cursor=pointer]:
            - button [ref=e691]:
              - img [ref=e692]
            - generic [ref=e694]:
              - img "BYD SEAGULL GS" [ref=e695]
              - generic [ref=e696]: "2026"
            - generic [ref=e697]:
              - generic [ref=e698]:
                - heading "BYD" [level=3] [ref=e699]
                - paragraph [ref=e700]: SEAGULL GS
              - generic [ref=e701]:
                - generic [ref=e702]:
                  - img [ref=e703]
                  - generic [ref=e706]: 1,600 KM
                - generic [ref=e707]:
                  - img [ref=e708]
                  - generic [ref=e711]: San José
              - generic [ref=e712]:
                - generic [ref=e713]:
                  - paragraph [ref=e714]: Precio
                  - generic [ref=e715]:
                    - generic [ref=e716]: ₡20,500
                    - generic [ref=e717]: $9,983,500
                - img [ref=e719]
        - button "Cargar más unidades" [ref=e722]
  - button "Open Next.js Dev Tools" [ref=e728] [cursor=pointer]:
    - img [ref=e729]
  - alert [ref=e732]
```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  | 
  3  | test.describe('Search Explorer Enhancements', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto('/search');
  6  |     // Wait for the page to load
  7  |     await page.waitForLoadState('networkidle');
  8  |   });
  9  | 
  10 |   test('should display improved search bar with new placeholder', async ({ page }) => {
  11 |     const searchBar = page.locator('input[placeholder="Marca, modelo, año, provincia o precio..."]');
  12 |     await expect(searchBar).toBeVisible();
  13 |     
  14 |     // Test clear button
  15 |     await searchBar.fill('Toyota');
  16 |     const clearButton = page.locator('button:has(svg.lucide-x)');
  17 |     await expect(clearButton).toBeVisible();
  18 |     await clearButton.click();
  19 |     await expect(searchBar).toHaveValue('');
  20 |   });
  21 | 
  22 |   test('should display year range string selector', async ({ page }) => {
  23 |     const yearSelect = page.locator('select:has-text("Todos los años")');
  24 |     await expect(yearSelect).toBeVisible();
  25 |   });
  26 | 
  27 |   test('should toggle between List and Tree view for brands', async ({ page }) => {
  28 |     // Default is list view
  29 |     const gridButton = page.locator('button:has(svg.lucide-grid)');
  30 |     const listButton = page.locator('button:has(svg.lucide-list)');
  31 |     
  32 |     await expect(gridButton).toHaveClass(/bg-cyan-600/); // Active
  33 |     
  34 |     // Switch to Tree view
  35 |     await listButton.click();
  36 |     await expect(listButton).toHaveClass(/bg-cyan-600/);
  37 |     
  38 |     // Check tree view elements (e.g., search within tree)
  39 |     const treeSearch = page.locator('input[placeholder="Filtrar marcas o modelos..."]');
  40 |     await expect(treeSearch).toBeVisible();
  41 |   });
  42 | 
  43 |   test('should display currency toggle and default to CRC', async ({ page }) => {
  44 |     // Check that both CRC and USD buttons exist
  45 |     const crcBtn = page.locator('button:has-text("CRC")');
  46 |     const usdBtn = page.locator('button:has-text("USD")');
  47 |     await expect(crcBtn).toBeVisible();
  48 |     await expect(usdBtn).toBeVisible();
  49 |     
  50 |     // By default, CRC should be active (emerald background)
  51 |     await expect(crcBtn).toHaveClass(/bg-emerald-600/);
  52 |     
  53 |     // Label should indicate CRC
  54 |     await expect(page.locator('label:has-text("Rango de Precio (CRC)")')).toBeVisible();
  55 |   });
  56 | 
  57 |   test('should update price range options when switching currency', async ({ page }) => {
  58 |     // By default CRC is selected, so the Min dropdown should have '₡2M'
  59 |     const minSelect = page.locator('select').filter({ hasText: 'Min' }).first();
  60 |     const maxSelect = page.locator('select').filter({ hasText: 'Max' }).last();
  61 |     
  62 |     // Check that '₡2M' option exists
> 63 |     await expect(minSelect.locator('option[value="2000000"]')).toBeVisible();
     |                                                                ^ Error: expect(locator).toBeVisible() failed
  64 |     
  65 |     // Switch to USD
  66 |     const usdBtn = page.locator('button:has-text("USD")');
  67 |     await usdBtn.click();
  68 |     
  69 |     // Label should indicate USD
  70 |     await expect(page.locator('label:has-text("Rango de Precio (USD)")')).toBeVisible();
  71 |     
  72 |     // Check that '$5k' option exists
  73 |     await expect(minSelect.locator('option[value="5000"]')).toBeVisible();
  74 |   });
  75 | 
  76 |   test('should display at least one data source', async ({ page }) => {
  77 |     // The label for data sources should be visible
  78 |     const sourceLabel = page.locator('label:has-text("Fuente de Datos")');
  79 |     await expect(sourceLabel).toBeVisible();
  80 |     
  81 |     // Check that there is at least one button in the container
  82 |     const sourceButtons = page.locator('div:has(> label:has-text("Fuente de Datos"))').locator('button');
  83 |     
  84 |     // Wait for at least one source button to be rendered (data from API)
  85 |     await expect(sourceButtons.first()).toBeVisible({ timeout: 15000 });
  86 |     
  87 |     const count = await sourceButtons.count();
  88 |     expect(count).toBeGreaterThan(0);
  89 |   });
  90 | });
  91 | 
```
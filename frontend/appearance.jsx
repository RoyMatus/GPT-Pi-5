import React, { useEffect, useLayoutEffect, useState } from 'react';
import { Field, Select, Switch, webLightTheme, webDarkTheme } from '@fluentui/react-components';
import { schemes, resolveAppearance, readAppearance, saveAppearance, appearanceVariables, mixColors } from './themes.mjs';

export function useAppearance() {
  const [appearance, setAppearance] = useState(()=>readAppearance());
  const [saved, setSaved] = useState(true);
  useLayoutEffect(()=>{
    const root=document.documentElement;
    root.dataset.theme=appearance.id;
    root.dataset.themeFinish=appearance.finish;
    root.style.colorScheme=appearance.light?'light':'dark';
    for(const [name,value] of Object.entries(appearanceVariables(appearance))) root.style.setProperty(name,value);
    setSaved(saveAppearance(undefined,appearance));
  },[appearance]);
  useEffect(()=>{
    const changed=event=>{if(event.key===null||['gpt-pi-scheme','gpt-pi-theme'].includes(event.key)) setAppearance(readAppearance());};
    window.addEventListener('storage',changed);
    return()=>window.removeEventListener('storage',changed);
  },[]);
  return {appearance,setAppearance,saved};
}

export function fluentAppearance(theme) {
  if(theme.isFluent) return {...(theme.light?webLightTheme:webDarkTheme),
    fontFamilyBase:'"Segoe UI", "GPT Pi Sans", sans-serif'};
  const base=theme.light?webLightTheme:webDarkTheme;
  const hover=mixColors(theme.panel,theme.control,.12), pressed=mixColors(theme.panel,theme.control,.2);
  const colors={...base};
  // Derive all interactive shades from the same palette, including Fluent portals.
  for(const key of Object.keys(colors)) {
    if(/^colorNeutralForeground[1-5](Hover|Pressed|Selected)?$/.test(key)) colors[key]=key.includes('1')?theme.text:theme.muted;
    if(/^colorNeutralBackground[1-6]$/.test(key)) colors[key]=theme.panel;
    if(/^colorNeutralBackground[1-6](Hover|Selected)$/.test(key)) colors[key]=hover;
    if(/^colorNeutralBackground[1-6]Pressed$/.test(key)) colors[key]=pressed;
    if(/^colorBrandForeground|^colorCompoundBrandForeground|^colorNeutralForeground[23]Brand/.test(key)) colors[key]=theme.control;
    if(/^colorBrandForegroundLink|^colorNeutralForeground2Link/.test(key)) colors[key]=theme.roles.link;
    if(/^colorBrandStroke|^colorCompoundBrandStroke/.test(key)) colors[key]=theme.control;
    if(/^colorNeutralStroke[12](Hover|Pressed|Selected)?$/.test(key)) colors[key]=mixColors(theme.panel,theme.text,.20);
    if(/^colorNeutralStrokeAccessible/.test(key)) colors[key]=theme.muted;
    if(/^colorBrandBackground2/.test(key)) colors[key]=hover;
    if(/^colorBrandBackground(Inverted)?(Hover|Pressed|Selected)?$/.test(key)) colors[key]=theme.control;
    if(/^colorCompoundBrandBackground/.test(key)) colors[key]=theme.control;
  }
  if(theme.id==='green_phosphor') {
    // Preserve warning/error icons and words while keeping the phosphor display monochrome.
    for(const key of Object.keys(colors)) if(/^color(Status|Palette)/.test(key)) {
      colors[key]=key.includes('Background')?theme.panel:theme.control;
    }
  }
  return {...colors,
    fontFamilyBase:'"Segoe UI", "GPT Pi Sans", sans-serif',
    colorNeutralForegroundOnBrand:theme.onControl,
    colorNeutralForegroundInverted:theme.onControl,
    colorNeutralBackgroundInverted:theme.control,
    colorNeutralBackgroundAlpha:theme.panel, colorNeutralBackgroundAlpha2:theme.panel,
    colorNeutralBackground4:theme.background,
    colorStrokeFocus1:theme.background,colorStrokeFocus2:theme.focus,
    colorNeutralForegroundDisabled:mixColors(theme.panel,theme.muted,.55),
    colorNeutralBackgroundDisabled:mixColors(theme.panel,theme.background,.5),
    borderRadiusSmall:'2px',borderRadiusMedium:'4px',borderRadiusLarge:'6px',borderRadiusXLarge:'8px',
  };
}

export function ThemePicker({appearance,onChange,saved=true,darkLabel=false}) {
  return <div className="theme-picker">
    <Field label="Графическая схема">
      <Select aria-label="Графическая схема" value={appearance.id}
        onChange={(_,data)=>onChange(resolveAppearance(data.value,appearance.light?'light':'dark'))}>
        {schemes.map(scheme=><option key={scheme.id} value={scheme.id}>{scheme.name}</option>)}
      </Select>
    </Field>
    <div className="theme-preview" style={appearanceVariables(appearance)}>
      <div className="theme-preview-swatches" aria-hidden="true">
        {[appearance.background,appearance.panel,appearance.control,appearance.roles.settings,appearance.text].map((color,index)=><span key={index} style={{background:color}} />)}
      </div>
      <strong>{appearance.name}</strong>
      <p>{appearance.description}</p>
    </div>
    {appearance.isFluent&&<Switch label={darkLabel?'Тёмная тема':'Светлая тема'}
      checked={darkLabel?!appearance.light:appearance.light}
      onChange={(_,data)=>onChange(resolveAppearance('fluent',(darkLabel?data.checked:!data.checked)?'dark':'light'))} />}
    {!saved&&<p role="status" className="theme-save-note">Выбор действует только на открытой странице: браузер не разрешает сохранение.</p>}
  </div>;
}

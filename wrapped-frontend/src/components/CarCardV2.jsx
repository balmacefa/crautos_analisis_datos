"use client"
import React from 'react';
import { motion } from 'framer-motion';
import { Fuel, Gauge, Calendar, ExternalLink, MapPin } from 'lucide-react';

export default function CarCardV2({ car }) {
  const { 
    marca, 
    modelo, 
    año, 
    precio_usd, 
    transmisión, 
    combustible, 
    kilometraje,
    url,
    informacion_general
  } = car;

  const provincia = informacion_general?.provincia || "Costa Rica";

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -5 }}
      className="group relative bg-[#1a1c1e] border border-white/5 rounded-2xl overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-300 flex flex-col h-full"
    >
      {/* Image Fallback Logic */}
      <div className="h-48 w-full bg-[#111] relative flex items-center justify-center overflow-hidden border-b border-white/5 group">
        <img
          src={
            informacion_general?.imagen_principal ||
            (informacion_general?.imagenes_secundarias && informacion_general.imagenes_secundarias[0]) ||
            car.imagen_principal ||
            (car.imagenes_secundarias && car.imagenes_secundarias[0]) ||
            '/images/car-placeholder.png'
          }
          alt={`${marca} ${modelo}`}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          onError={(e) => { e.target.src = '/images/car-placeholder.png'; }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20" />
      </div>

      <div className="p-5 flex flex-col flex-1">
        <div className="flex justify-between items-start mb-2">
          <div>
            <span className="text-[10px] text-blue-400 font-bold uppercase tracking-widest">{marca}</span>
            <h3 className="text-xl font-bold text-white group-hover:text-blue-400 transition-colors leading-tight">
              {modelo}
            </h3>
          </div>
          <motion.div whileTap={{ scale: 0.9 }}>
            <a 
              href={url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-2 bg-white/5 hover:bg-blue-600 rounded-full transition-colors text-white/50 hover:text-white"
            >
              <ExternalLink size={16} />
            </a>
          </motion.div>
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          <Badge icon={<Calendar size={12} />} text={año} />
          <Badge icon={<MapPin size={12} />} text={provincia} />
          {transmisión && <Badge text={transmisión} />}
        </div>

        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="space-y-1">
            <p className="text-[10px] text-white/30 uppercase font-bold flex items-center gap-1">
              <Fuel size={10} /> Combustible
            </p>
            <p className="text-sm font-semibold">{combustible || 'N/A'}</p>
          </div>
          <div className="space-y-1 text-right">
            <p className="text-[10px] text-white/30 uppercase font-bold flex items-center gap-1 justify-end">
              <Gauge size={10} /> Kilometraje
            </p>
            <p className="text-sm font-semibold">{kilometraje || 'Consultar'}</p>
          </div>
        </div>

        <div className="mt-auto pt-4 border-t border-white/5 flex items-center justify-between">
          <p className="text-2xl font-black text-white tracking-tighter">
            ${precio_usd?.toLocaleString() || '---'} <span className="text-xs text-white/40 font-bold ml-1 uppercase">USD</span>
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function Badge({ icon, text }) {
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1 bg-white/5 border border-white/10 rounded-lg text-xs font-medium text-white/70">
      {icon}
      {text}
    </div>
  );
}

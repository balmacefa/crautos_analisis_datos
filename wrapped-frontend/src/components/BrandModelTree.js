"use client"
import React, { useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, CheckSquare, Square, Search } from 'lucide-react';
import { cn } from '@/lib/utils';

export function BrandModelTree({ 
  data, 
  selectedBrands = [], 
  selectedModels = [],
  onSelectBrand,
  onSelectModel,
  onClear
}) {
  const [expandedBrands, setExpandedBrands] = useState({});
  const [searchTerm, setSearchTerm] = useState('');

  const tree = useMemo(() => {
    const brands = {};
    data.forEach(item => {
      if (!brands[item.marca]) {
        brands[item.marca] = {
          name: item.marca,
          count: 0,
          models: []
        };
      }
      brands[item.marca].count += item.count;
      brands[item.marca].models.push({
        name: item.modelo,
        count: item.count
      });
    });
    return Object.values(brands).sort((a, b) => b.count - a.count);
  }, [data]);

  const filteredTree = useMemo(() => {
    if (!searchTerm) return tree;
    const term = searchTerm.toLowerCase();
    return tree.map(brand => {
      const brandMatches = brand.name.toLowerCase().includes(term);
      const matchingModels = brand.models.filter(m => m.name.toLowerCase().includes(term));
      
      if (brandMatches || matchingModels.length > 0) {
        return {
          ...brand,
          models: brandMatches ? brand.models : matchingModels,
          isMatch: brandMatches
        };
      }
      return null;
    }).filter(Boolean);
  }, [tree, searchTerm]);

  const toggleBrand = (brandName) => {
    setExpandedBrands(prev => ({
      ...prev,
      [brandName]: !prev[brandName]
    }));
  };

  return (
    <div className="space-y-4">
      <div className="relative group">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-cyan-400 transition-colors" size={14} />
        <input 
          type="text"
          placeholder="Filtrar marcas o modelos..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl py-2 pl-9 pr-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-cyan-500/50 transition-all placeholder:text-white/20"
        />
      </div>

      <div className="max-h-80 overflow-y-auto pr-2 custom-scrollbar space-y-1">
        {filteredTree.map(brand => {
          const isExpanded = expandedBrands[brand.name] || (searchTerm && brand.models.length > 0);
          const isBrandSelected = selectedBrands.includes(brand.name);
          
          return (
            <div key={brand.name} className="space-y-1">
              <div 
                className={cn(
                  "flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors group",
                  isBrandSelected ? "bg-cyan-500/10" : "hover:bg-white/5"
                )}
                onClick={() => toggleBrand(brand.name)}
              >
                <div className="flex items-center gap-2">
                  <div 
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectBrand(brand.name);
                    }}
                    className="p-1 hover:bg-white/10 rounded transition-colors"
                  >
                    {isBrandSelected ? (
                      <CheckSquare size={16} className="text-cyan-400" />
                    ) : (
                      <Square size={16} className="text-white/20" />
                    )}
                  </div>
                  <span className={cn(
                    "text-xs font-bold",
                    isBrandSelected ? "text-cyan-400" : "text-white/80"
                  )}>
                    {brand.name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-white/20 font-mono">{brand.count}</span>
                  {isExpanded ? <ChevronDown size={14} className="text-white/20" /> : <ChevronRight size={14} className="text-white/20" />}
                </div>
              </div>

              {isExpanded && (
                <div className="ml-6 space-y-1 border-l border-white/10 pl-2">
                  {brand.models.map(model => {
                    const isModelSelected = selectedModels.includes(model.name);
                    return (
                      <div 
                        key={model.name}
                        onClick={() => onSelectModel(model.name)}
                        className={cn(
                          "flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors",
                          isModelSelected ? "bg-white/10 text-cyan-400" : "text-white/50 hover:bg-white/5 hover:text-white"
                        )}
                      >
                        <span className="text-[11px]">{model.name}</span>
                        <span className="text-[9px] font-mono opacity-40">{model.count}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

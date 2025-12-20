// Device Selector Component

import { DeviceType } from '../types/analysis.js';

const devices: DeviceType[] = [
  { 
    id: 'pMDI_type1', 
    name: 'pMDI_type1', 
    description: 'pMDI_type1(기본 가스분사 스프레이 구조) - Ventolin Evohaler, Flixotide Evohaler, Seretide Evohaler, Symbicort Rapihaler, Flutiform Inhaler' 
  },
  { 
    id: 'pMDI_type2', 
    name: 'pMDI_type2', 
    description: 'pMDI_type2(미세입자 분무 정밀 스프레이 구조) - Alvesco Inhaler, Foster' 
  },
  { 
    id: 'DPI_type1', 
    name: 'DPI_type1', 
    description: 'DPI_type1(내부 분말분산 건조분말 구조) - Anoro Ellipta, Relvar Ellipta, Incruse Ellipta, Trelegy Ellipta, Foster Nexthaler' 
  },
  { 
    id: 'DPI_type2', 
    name: 'DPI_type2', 
    description: 'DPI_type2(레버·다이얼 건조분말 구조) - Eklira Genuair, Duaklir Genuair, Symbicort Turbuhaler, Pulmicort Turbuhaler' 
  },
  { 
    id: 'DPI_type3', 
    name: 'DPI_type3', 
    description: 'DPI_type3(캡슐형 건조분말 구조) - Xoterna Breezhaler, Spiriva Handihaler' 
  },
  { 
    id: 'SMI_type1', 
    name: 'SMI_type1', 
    description: 'SMI_type1(미세 안개 분사 연무흡입기 구조) - Vahelva Respimat, Spiriva Respimat' 
  }
];

export class DeviceSelector {
  private deviceBtn: HTMLButtonElement;
  private dropdown: HTMLElement;
  private selectedDevice: DeviceType | null = null;
  private onSelectCallback?: (device: DeviceType) => void;

  constructor() {
    this.deviceBtn = document.getElementById('deviceSelect') as HTMLButtonElement;
    this.dropdown = document.getElementById('deviceDropdown') as HTMLElement;
    this.init();
  }

  private init(): void {
    // Toggle dropdown
    this.deviceBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleDropdown();
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
      this.hideDropdown();
    });

    // Device selection
    const dropdownItems = this.dropdown.querySelectorAll('.dropdown-item');
    dropdownItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.stopPropagation();
        const deviceId = (item as HTMLElement).dataset.deviceId as DeviceType['id'];
        const device = devices.find(d => d.id === deviceId);
        if (device) {
          this.selectDevice(device);
        }
      });
    });
  }

  private toggleDropdown(): void {
    const isVisible = this.dropdown.style.display !== 'none';
    if (isVisible) {
      this.hideDropdown();
    } else {
      this.showDropdown();
    }
  }

  private showDropdown(): void {
    this.dropdown.style.display = 'block';
    this.deviceBtn.classList.add('active');
  }

  private hideDropdown(): void {
    this.dropdown.style.display = 'none';
    this.deviceBtn.classList.remove('active');
  }

  private selectDevice(device: DeviceType): void {
    this.selectedDevice = device;
    
    // Update UI - mark selected item
    const dropdownItems = this.dropdown.querySelectorAll('.dropdown-item');
    dropdownItems.forEach(item => {
      const itemDeviceId = (item as HTMLElement).dataset.deviceId;
      if (itemDeviceId === device.id) {
        item.classList.add('selected');
      } else {
        item.classList.remove('selected');
      }
    });

    // Hide dropdown
    this.hideDropdown();

    // Trigger callback
    if (this.onSelectCallback) {
      this.onSelectCallback(device);
    }
  }

  public onSelect(callback: (device: DeviceType) => void): void {
    this.onSelectCallback = callback;
  }

  public getSelectedDevice(): DeviceType | null {
    return this.selectedDevice;
  }

  public reset(): void {
    this.selectedDevice = null;
    const dropdownItems = this.dropdown.querySelectorAll('.dropdown-item');
    dropdownItems.forEach(item => item.classList.remove('selected'));
  }
}



# PyTorch configuration with ROCm FOR AMD ONLY!

* **Dual Boot Linux/Ubuntu Image 22.04.4 LTS**: This is the OS that got used for using machine - learning training with Object Detection.

* **Installing AMD drivers -- System dependencies**
>wget https://repo.radeon.com/amdgpu-install/6.0/ubuntu/jammy/amdgpu-install_6.0.60000-1_all.deb
>sudo apt install ./amdgpu-install_6.0.60000-1_all.deb

* **Installing drivers for ROCm -- System dependencies**
>sudo amdgpu-install --usecase=rocm

* **OpenGL library -- System dependencies**
>sudo apt install libgl1-mesa-glx libglib2.0-0

* **Did this not as an $ROOT but &USER so i needed to give myself permissions to render and video group by**:
>sudo usermod -a -G render $USER
>sudo usermod -a -G video $USER

* **Used venv_linux for activating the environment for training but first i got to the root path of the projects folder through command**: 
>cd /path/toyourProject
>cd /path/Skole/bacheloroppgave 

* **Created the virtual environment by this command**:
>python3 -m venv venv_linux

* **Command to active local environment (python environment):**
>source venv_linux/bin/activate 

* **Installing PyTorch within the virtual environment**:
> pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0

* **CRUCIAL STEP: For some reason, i needed to export the HSA Override function -> Hardware Emulation since my GPU was not supported officially by ROCm. So without the correct command provided, the training wouldn't work. (6000 - Series)*:
> export HSA_OVERRIDE_GFX_VERSION=10.3.0 

* **Command to actually to use the script train.py**: This will and initated the training of the photos we got in the folders of train,val & test.
>python3 train.py





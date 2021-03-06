#!/bin/bash --login
#PBS -j oe
#PBS -q charon
#PBS -l select=1:ncpus=1:mem=2gb
#PBS -l walltime=00:10:00
# # disabled option -l place=excl
# interactive for testing
# qsub -j oe -q charon -l select=1:ncpus=1:mem=2gb -l walltime=00:59:00 -I
# qsub -j oe -l select=1:ncpus=1:mem=2gb -l walltime=00:59:00 -I

module load python-3.6.2-gcc
module load python36-modules-gcc

echo "installing pip packages: <ci-hpc-install>"
<ci-hpc-install>

NOW=$(date "+%Y-%m-%d_%H-%M-%S")

# print some debug info
echo "[$NOW] running installation script"
if [[ -n "$PBS_JOBID" ]]; then
  echo "Running job $PBS_JOBNAME ($PBS_JOBID) in `pwd`"
  echo "Time: `date`"
  echo "Running on master node: `hostname`"
  echo "Using nodefile :         $PBS_NODEFILE"
  cat $PBS_NODEFILE
else
  echo "Running job on frontend in `pwd`"
  echo "Time: `date`"
  echo "Running on master node: `hostname`"
fi
echo "#################################################"

# ------------------------------------------------------------------------------
# the following placeholder will be replaced later on
echo "<ci-hpc-exec>"
<ci-hpc-exec>

exit $?

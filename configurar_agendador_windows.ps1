# Tarefa 1: Segunda a Sexta-feira (07:00 às 22:00, a cada 45 minutos)
$action1 = New-ScheduledTaskAction -Execute "wscript.exe" -Argument '"""c:\Users\marcelo.guedes\Grupo Fapes Projetos\Dr Hoje\dr-hoje-dashboard\disparar_silencioso.vbs"""'
$trigger1 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 07:00
$trigger1.Repetition = (New-ScheduledTaskTrigger -Once -At 07:00 -RepetitionInterval (New-TimeSpan -Minutes 45) -RepetitionDuration (New-TimeSpan -Hours 15)).Repetition
Register-ScheduledTask -TaskName "Atualizar_Dashboard_DrHoje_Semana" -Action $action1 -Trigger $trigger1 -Force

# Tarefa 2: Sábados e Domingos (08:00 às 22:00, a cada 4 horas)
$action2 = New-ScheduledTaskAction -Execute "wscript.exe" -Argument '"""c:\Users\marcelo.guedes\Grupo Fapes Projetos\Dr Hoje\dr-hoje-dashboard\disparar_silencioso.vbs"""'
$trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday,Sunday -At 08:00
$trigger2.Repetition = (New-ScheduledTaskTrigger -Once -At 08:00 -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration (New-TimeSpan -Hours 14)).Repetition
Register-ScheduledTask -TaskName "Atualizar_Dashboard_DrHoje_FimDeSemana" -Action $action2 -Trigger $trigger2 -Force

Write-Host "DE SEGUNDA A SEXTA: A cada 45 minutos (07:00 às 22:00) - REGISTRADO!"
Write-Host "FINAIS DE SEMANA: A cada 4 horas (08:00 às 22:00) - REGISTRADO!"
